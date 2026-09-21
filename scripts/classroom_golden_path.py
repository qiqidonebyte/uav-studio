#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time
import uuid

import httpx


@dataclass
class Student:
    index: int
    client: httpx.Client
    user_id: int
    username: str
    run_id: int | None = None


def wait_until(fn, *, timeout: float, interval: float = 0.25, description: str = "condition"):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = fn()
        if last:
            return last
        time.sleep(interval)
    raise RuntimeError(f"timeout waiting for {description}; last={last!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="UAV Studio 1 teacher + 35 students golden path")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--admin-password", required=True)
    parser.add_argument("--students", type=int, default=35)
    parser.add_argument("--expected-slots", type=int, default=12)
    parser.add_argument("--exercise-px4", action="store_true", help="Actually Arm/Takeoff/Hover/Land every run")
    parser.add_argument("--px4-timeout", type=float, default=60.0)
    args = parser.parse_args()

    suffix = uuid.uuid4().hex[:8]
    password = "Classroom123!"
    admin = httpx.Client(base_url=args.base_url, timeout=20.0)
    login = admin.post("/api/auth/login", json={"username": "admin", "password": args.admin_password})
    login.raise_for_status()

    teacher_username = f"gold_teacher_{suffix}"
    teacher = httpx.Client(base_url=args.base_url, timeout=20.0)
    teacher_register = teacher.post("/api/auth/register", json={
        "username": teacher_username,
        "display_name": "Golden Teacher",
        "password": password,
    })
    teacher_register.raise_for_status()
    teacher_id = teacher_register.json()["user"]["id"]
    role = admin.patch(f"/api/admin/users/{teacher_id}/role", json={"role": "teacher"})
    role.raise_for_status()
    teacher.post("/api/auth/logout")
    teacher = httpx.Client(base_url=args.base_url, timeout=20.0)
    teacher.post("/api/auth/login", json={"username": teacher_username, "password": password}).raise_for_status()

    classroom = teacher.post("/api/teacher/classes", json={
        "name": f"Golden Path {suffix}",
        "academic_year": "2026-2027-1",
    })
    classroom.raise_for_status()
    classroom_data = classroom.json()

    students: list[Student] = []
    for index in range(args.students):
        client = httpx.Client(base_url=args.base_url, timeout=20.0)
        username = f"gold_s{index+1:02d}_{suffix}"
        response = client.post("/api/auth/register", json={
            "username": username,
            "display_name": f"Golden Student {index+1:02d}",
            "password": password,
        })
        response.raise_for_status()
        user_id = response.json()["user"]["id"]
        join = client.post("/api/training/classes/join", json={"invite_code": classroom_data["invite_code"]})
        join.raise_for_status()
        students.append(Student(index=index, client=client, user_id=user_id, username=username))

    assignment = teacher.post("/api/teacher/assignments", json={
        "class_id": classroom_data["id"],
        "title": "Golden Path 综合故障诊断",
        "scenario_id": "F06_INTEGRATED",
        "description": "并发可靠性自动测试",
        "requirements": {"diagnosis": True, "repair": True, "prearm": True, "flight_validation": True},
        "score_weights": {"case_score": 70, "flight_validation": 20, "operation_norm": 10},
    })
    assignment.raise_for_status()
    assignment_id = assignment.json()["id"]

    def start_and_submit(student: Student) -> int:
        started = student.client.post(f"/api/training/assignments/{assignment_id}/start", json={"aircraft_id": None})
        started.raise_for_status()
        student.run_id = started.json()["id"]
        submitted = student.client.post(f"/api/training/runs/{student.run_id}/submit", json={
            "passed": True,
            "score": 88,
            "elapsed_seconds": 600,
            "hints_used": 1,
            "wrong_operations": 1,
            "prearm_passed": True,
            "flight_validation_passed": False,
            "result": {
                "visited_sections": ["rc", "power", "safety", "preflight"],
                "condition_state": {"preflight_passed": True},
                "evaluation": {"score": 88},
            },
        })
        submitted.raise_for_status()
        assert submitted.json()["status"] == "awaiting_flight"
        return student.run_id

    with ThreadPoolExecutor(max_workers=min(20, args.students)) as executor:
        list(executor.map(start_and_submit, students))

    def acquire(student: Student):
        assert student.run_id is not None
        response = student.client.post(f"/api/training/runs/{student.run_id}/px4/session")
        response.raise_for_status()
        return response.json()

    with ThreadPoolExecutor(max_workers=min(20, args.students)) as executor:
        sessions = list(executor.map(acquire, students))

    assigned = [item for item in sessions if item.get("slot_id") is not None]
    queued = [item for item in sessions if item.get("status") == "queued"]
    if len(assigned) != min(args.expected_slots, args.students):
        raise RuntimeError(f"expected {args.expected_slots} assigned slots, got {len(assigned)}")
    if len({item["slot_id"] for item in assigned}) != len(assigned):
        raise RuntimeError("duplicate PX4 slot assignment detected")
    print(f"PASS capacity: active={len(assigned)} queued={len(queued)}")

    pool = teacher.get("/api/teacher/px4-pool")
    pool.raise_for_status()
    payload = pool.json()
    if payload["pool_size"] != args.expected_slots:
        raise RuntimeError(f"pool_size={payload['pool_size']} expected={args.expected_slots}")
    print(f"PASS teacher pool view: {payload['used']}/{payload['pool_size']} used, queued={payload['queued']}")

    if args.exercise_px4:
        pending = list(students)
        while pending:
            active: list[Student] = []
            for student in list(pending):
                assert student.run_id is not None
                status = student.client.get(f"/api/training/runs/{student.run_id}/px4/status")
                status.raise_for_status()
                body = status.json()
                if body.get("connected"):
                    active.append(student)
                    if len(active) >= args.expected_slots:
                        break
            if not active:
                time.sleep(1)
                continue

            def fly(student: Student):
                assert student.run_id is not None
                base = f"/api/training/runs/{student.run_id}/px4"
                student.client.post(f"{base}/request-streams").raise_for_status()
                student.client.post(f"{base}/prearm-check").raise_for_status()
                arm = student.client.post(f"{base}/arm")
                arm.raise_for_status()
                takeoff = student.client.post(f"{base}/takeoff", json={"altitude_m": 2.0})
                takeoff.raise_for_status()

                def airborne():
                    telemetry = student.client.get(f"{base}/telemetry")
                    telemetry.raise_for_status()
                    z = float(telemetry.json().get("local_position", {}).get("z", 0.0) or 0.0)
                    return z > 1.0

                wait_until(airborne, timeout=args.px4_timeout, description=f"{student.username} takeoff")
                time.sleep(1.5)
                student.client.post(f"{base}/land").raise_for_status()

                def landed():
                    telemetry = student.client.get(f"{base}/telemetry")
                    telemetry.raise_for_status()
                    body = telemetry.json()
                    z = float(body.get("local_position", {}).get("z", 0.0) or 0.0)
                    return z < 0.25

                wait_until(landed, timeout=args.px4_timeout, description=f"{student.username} land")
                validation = student.client.post(
                    f"/api/training/runs/{student.run_id}/flight-validation",
                    json={"passed": True, "detail": "Golden Path: Arm → Takeoff → Hover → Land"},
                )
                validation.raise_for_status()
                if validation.json()["status"] != "completed":
                    raise RuntimeError(f"{student.username} did not complete")
                return student

            with ThreadPoolExecutor(max_workers=len(active)) as executor:
                finished = list(executor.map(fly, active))
            for student in finished:
                pending.remove(student)
            print(f"PX4 batch complete: finished={args.students-len(pending)}/{args.students}")
    else:
        # Data-chain completion only. Real PX4 flight is intentionally optional.
        for student in students:
            assert student.run_id is not None
            response = student.client.post(
                f"/api/training/runs/{student.run_id}/flight-validation",
                json={"passed": True, "detail": "Golden Path data-chain completion (PX4 exercise disabled)"},
            )
            response.raise_for_status()

    gradebook = teacher.get("/api/teacher/gradebook", params={"class_id": classroom_data["id"]})
    gradebook.raise_for_status()
    data = gradebook.json()
    if data["student_count"] != args.students:
        raise RuntimeError(f"gradebook student_count={data['student_count']}")
    if args.exercise_px4 and data["completion_rate"] != 100.0:
        raise RuntimeError(f"completion_rate={data['completion_rate']}")
    print(f"PASS gradebook: students={data['student_count']} completion={data['completion_rate']}%")
    print("GOLDEN PATH PASS")


if __name__ == "__main__":
    main()
