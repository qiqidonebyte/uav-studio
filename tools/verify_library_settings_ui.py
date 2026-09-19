from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "App nav: 组件库": ("frontend/src/App.vue", 'to="/components"'),
    "App nav: 系统设置": ("frontend/src/App.vue", 'to="/settings"'),
    "Router: components": ("frontend/src/router/index.ts", "path: '/components'"),
    "Router: settings": ("frontend/src/router/index.ts", "path: '/settings'"),
    "Component library search": ("frontend/src/views/ComponentLibrary.vue", 'class="library-search"'),
    "Component library 3D preview": ("frontend/src/views/ComponentLibrary.vue", '<ComponentPreview'),
    "Component library compatibility": ("frontend/src/views/ComponentLibrary.vue", "适配关系"),
    "Component library editor": ("frontend/src/views/ComponentLibrary.vue", "工程参数 JSON"),
    "Settings account": ("frontend/src/views/Settings.vue", "账户与密码"),
    "Settings general": ("frontend/src/views/Settings.vue", "通用设置"),
    "Settings display": ("frontend/src/views/Settings.vue", "3D 显示"),
    "Settings flight": ("frontend/src/views/Settings.vue", "飞行实验"),
    "Settings about": ("frontend/src/views/Settings.vue", "关于"),
    "Flight safety guard preserved": ("frontend/src/views/FlightLab.vue", "flightControlAvailability"),
    "Flight settings applied": ("frontend/src/views/FlightLab.vue", "default_altitude_m"),
    "3D settings applied": ("frontend/src/components/DroneScene.vue", "applyDisplaySettings"),
    "3D grid toggle wired": ("frontend/src/components/DroneScene.vue", "settings.show_grid"),
    "Chart window wired": ("frontend/src/components/RealtimeCharts.vue", "windowSeconds"),
    "Assembly component refresh": ("frontend/src/stores/assembly.ts", "refreshComponents"),
}

failed = []
for label, (relative, needle) in checks.items():
    text = (ROOT / relative).read_text(encoding="utf-8")
    if needle not in text:
        failed.append(f"{label}: missing {needle!r} in {relative}")
    else:
        print(f"PASS {label}")

if failed:
    print("\nFAILED")
    for item in failed:
        print(" -", item)
    raise SystemExit(1)

print(f"\nUI contract verification PASS: {len(checks)} checks")
