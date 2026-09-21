<template>
  <div class="debug-page">
    <aside class="debug-sidebar">
      <section class="side-section">
        <div class="side-title">调试流程</div>
        <button
          v-for="(step, index) in steps"
          :key="step.key"
          :class="['flow-step', { active: activeSection === step.key }]"
          @click="activeSection = step.key"
        >
          <span class="step-no">{{ index + 1 }}</span>
          <span class="step-icon">{{ step.icon }}</span>
          <span class="step-copy">
            <b>{{ step.title }}</b>
            <small>{{ step.subtitle }}</small>
          </span>
        </button>
      </section>

      <section class="side-section scenarios training-sidebar-section">
        <div class="side-title training-side-title">
          <span>实训案例库</span>
          <small>{{ trainingCases.length }} 个案例</small>
        </div>
        <button
          :class="['scenario-card', { active: !activeTrainingCase }]"
          @click="enterFreeDebug"
        >
          <span>◇</span>
          <div><b>自由调试</b><small>不注入故障，自主使用调试工具</small></div>
        </button>
        <button
          v-if="activeTrainingCase"
          class="scenario-card active training-current-card"
          @click="trainingLibraryOpen = true"
        >
          <span>{{ activeTrainingCase.icon }}</span>
          <div>
            <b>{{ activeTrainingCase.id }} · {{ activeTrainingCase.title }}</b>
            <small>{{ trainingElapsedText }} · {{ trainingProgressText }}</small>
          </div>
        </button>
        <button class="training-library-button" @click="trainingLibraryOpen = true">
          <span>▦</span>
          <div><b>打开案例库</b><small>基础故障 / 综合检修</small></div>
          <strong>›</strong>
        </button>
        <small v-if="trainingCatalogError" class="training-catalog-error">{{ trainingCatalogError }}</small>
      </section>

      <div class="practice-mark">
        <b>PRACTICE</b>
        <span>MAKE BETTER PILOTS</span>
      </div>
    </aside>

    <main class="debug-main">
      <div class="section-tabs">
        <button
          v-for="tab in topTabs"
          :key="tab.key"
          :class="{ active: activeSection === tab.key }"
          @click="activeSection = tab.key"
        >{{ tab.title }}</button>
      </div>

      <section v-if="activeTrainingCase" class="training-task-hud">
        <div class="training-task-main">
          <span class="training-case-code">{{ activeTrainingCase.id }}</span>
          <div>
            <b>{{ activeTrainingCase.title }}</b>
            <small>{{ activeTrainingCase.student_brief.symptom }}</small>
          </div>
        </div>
        <div class="training-task-meta">
          <div><span>计时</span><b>{{ trainingElapsedText }}</b></div>
          <div><span>建议</span><b>{{ activeTrainingCase.recommended_minutes }} min</b></div>
          <div><span>进度</span><b>{{ trainingProgressText }}</b></div>
          <div><span>故障源</span><b>{{ activeTrainingCase.fault_source }}</b></div>
        </div>
        <div class="training-task-actions">
          <button @click="requestTrainingHint">提示 {{ trainingHintsUsed }}/{{ activeTrainingCase.hints.length }}</button>
          <button class="training-submit" @click="submitTrainingCase">提交诊断</button>
          <button @click="restartTrainingCase">重新开始</button>
          <button class="training-exit" @click="enterFreeDebug">退出案例</button>
        </div>
        <div v-if="trainingRemoteStatus" class="training-hint"><b>课程记录</b><span>{{ trainingRemoteStatus }}</span></div>
        <div v-if="trainingCurrentHint" class="training-hint"><b>提示</b><span>{{ trainingCurrentHint }}</span></div>
        <div v-if="trainingSubmittedEvaluation" :class="['training-result', { passed: trainingSubmittedEvaluation.passed }]">
          <div>
            <b>{{ trainingSubmittedEvaluation.passed ? '案例完成' : '尚未完成全部修复' }}</b>
            <small>修复 {{ trainingSubmittedEvaluation.repairCompleted }}/{{ trainingSubmittedEvaluation.repairTotal }} · 验证 {{ trainingSubmittedEvaluation.validationCompleted }}/{{ trainingSubmittedEvaluation.validationTotal }}</small>
          </div>
          <strong>{{ trainingSubmittedEvaluation.score }}<em>/100</em></strong>
          <span>诊断 {{ trainingSubmittedEvaluation.diagnosisScore }} · 修复 {{ trainingSubmittedEvaluation.repairScore }} · 验证 {{ trainingSubmittedEvaluation.validationScore }} · 效率 {{ trainingSubmittedEvaluation.efficiencyScore }} · 扣分 {{ trainingSubmittedEvaluation.penalty }}</span>
        </div>
      </section>

      <DiagnosisWorksheet
        ref="diagnosisWorksheetRef"
        :user-id="auth.user?.id ?? null"
        :role="learningRole"
        :run-id="assignedRunId"
        :scenario-id="activeTrainingCase?.id || assignedScenarioId || scenario"
        :scenario-title="activeTrainingCase?.title || '自由调试'"
        :symptom="activeTrainingCase?.student_brief.symptom || ''"
        @ready-change="diagnosisWorksheetReady = $event"
        @saved="diagnosisWorksheetSaved = true"
      />

      <template v-if="activeSection === 'sensors'">
        <div class="sensor-workbench">
          <section class="surface sensor-hero-surface">
            <div class="surface-heading">
              <div><span class="heading-icon">◈</span><b>飞控姿态 / IMU 实时监视</b></div>
              <span class="heading-note">{{ bridgeMode === 'live' ? 'PX4 MAVLink 实时数据' : '教学模拟数据' }}</span>
            </div>

            <div class="sensor-hero-grid">
              <div class="attitude-panel">
                <div class="attitude-shell" aria-label="姿态仪">
                  <div class="attitude-moving" :style="{ transform: attitudeTransform }">
                    <div class="attitude-sky"></div>
                    <div class="attitude-ground"></div>
                    <div class="attitude-horizon"></div>
                  </div>
                  <div class="attitude-pitch-mark pitch-plus">+10°</div>
                  <div class="attitude-pitch-mark pitch-zero">0°</div>
                  <div class="attitude-pitch-mark pitch-minus">−10°</div>
                  <div class="attitude-aircraft"><i></i><span></span><i></i></div>
                  <div class="attitude-heading">HDG {{ headingText }}</div>
                </div>
                <div class="attitude-readouts">
                  <div><span>ROLL</span><b>{{ rollDegText }}</b></div>
                  <div><span>PITCH</span><b>{{ pitchDegText }}</b></div>
                  <div><span>YAW</span><b>{{ yawDegText }}</b></div>
                </div>
              </div>

              <div class="fc-overview">
                <div class="fc-status-row">
                  <div class="fc-chip"><span>飞控</span><b>{{ bridgeMode === 'live' ? 'PX4 SIH' : '教学模拟' }}</b></div>
                  <div class="fc-chip"><span>模式</span><b>{{ px4ModeText }}</b></div>
                  <div class="fc-chip"><span>System ID</span><b>{{ liveTelemetry?.system_id ?? '—' }}</b></div>
                  <div class="fc-chip"><span>Heartbeat</span><b>{{ heartbeatText }}</b></div>
                </div>

                <div class="imu-block">
                  <div class="sensor-block-title">
                    <div><b>IMU 三轴数据</b><small>{{ imuSourceText }}</small></div>
                    <span :class="['sensor-status-pill', imuHealthClass]">{{ imuHealthText }}</span>
                  </div>
                  <div class="vector-table">
                    <div class="vector-head"><span>轴</span><span>加速度 m/s²</span><span>角速度 rad/s</span></div>
                    <div v-for="axis in sensorAxes" :key="axis" class="vector-row">
                      <b>{{ axis.toUpperCase() }}</b>
                      <span>{{ formatSensorValue(imuAccel[axis], 3) }}</span>
                      <span>{{ formatSensorValue(imuGyro[axis], 4) }}</span>
                    </div>
                  </div>
                  <div class="imu-footer">
                    <span>温度 <b>{{ temperatureText }}</b></span>
                    <span>数据延迟 <b>{{ imuAgeText }}</b></span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <div class="sensor-card-grid">
            <section class="surface sensor-card">
              <div class="sensor-card-head">
                <div><span class="sensor-card-icon">⌖</span><b>GNSS / GPS</b></div>
                <span :class="['sensor-status-pill', sensorStatusClass('gps')]">{{ sensorStatusText('gps') }}</span>
              </div>
              <div class="sensor-kpi-row">
                <div><span>Fix</span><b>{{ gpsFixText }}</b></div>
                <div><span>卫星</span><b>{{ gpsSatelliteText }}</b></div>
                <div><span>EPH</span><b>{{ gpsEphText }}</b></div>
              </div>
              <dl class="sensor-detail-list">
                <div><dt>纬度</dt><dd>{{ latitudeText }}</dd></div>
                <div><dt>经度</dt><dd>{{ longitudeText }}</dd></div>
                <div><dt>相对高度</dt><dd>{{ globalAltitudeText }}</dd></div>
              </dl>
            </section>

            <section class="surface sensor-card" :class="{ 'sensor-card-fault': compassFaultActive }">
              <div class="sensor-card-head">
                <div><span class="sensor-card-icon">◉</span><b>磁罗盘 / 航向</b></div>
                <span :class="['sensor-status-pill', sensorStatusClass('magnetometer')]">{{ sensorStatusText('magnetometer') }}</span>
              </div>
              <div class="compass-display">
                <div class="compass-ring">
                  <span class="north">N</span><span class="east">E</span><span class="south">S</span><span class="west">W</span>
                  <i :style="{ transform: `rotate(${headingDegrees}deg)` }"></i>
                  <b>{{ headingText }}</b>
                </div>
                <div class="mag-values">
                  <div><span>磁场强度</span><b>{{ magneticFieldText }}</b></div>
                  <div><span>X / Y / Z</span><b>{{ magneticVectorText }}</b></div>
                </div>
              </div>
              <div v-if="compassFaultActive" class="inline-sensor-warning">检测到教学罗盘异常：完成罗盘校准后重新检查 EKF。</div>
            </section>

            <section class="surface sensor-card">
              <div class="sensor-card-head">
                <div><span class="sensor-card-icon">◒</span><b>气压计</b></div>
                <span :class="['sensor-status-pill', sensorStatusClass('barometer')]">{{ sensorStatusText('barometer') }}</span>
              </div>
              <div class="large-sensor-number"><b>{{ pressureAltitudeText }}</b><span>气压高度</span></div>
              <dl class="sensor-detail-list">
                <div><dt>绝对气压</dt><dd>{{ pressureText }}</dd></div>
                <div><dt>温度</dt><dd>{{ baroTemperatureText }}</dd></div>
                <div><dt>数据延迟</dt><dd>{{ barometerAgeText }}</dd></div>
              </dl>
            </section>

            <section class="surface sensor-card">
              <div class="sensor-card-head">
                <div><span class="sensor-card-icon">◎</span><b>EKF / 状态估计</b></div>
                <span :class="['sensor-status-pill', ekfOk ? 'ok' : 'warn']">{{ ekfText }}</span>
              </div>
              <div class="ekf-state-block">
                <div><span>Estimator Flags</span><b>{{ estimatorFlagsText }}</b></div>
                <div><span>本地位置 X / Y / Z</span><b>{{ localPositionText }}</b></div>
                <div><span>Pre-Arm</span><b :class="prearmPassed ? 'ok-text' : 'warn-text'">{{ prearmPassed ? '通过' : '阻断' }}</b></div>
              </div>
              <div :class="['ekf-summary', ekfOk ? 'pass' : 'fail']">{{ ekfDiagnosisText }}</div>
            </section>
          </div>

          <section class="surface calibration-surface">
            <div class="surface-heading">
              <div><span class="heading-icon">⚙</span><b>传感器校准与诊断</b></div>
              <button class="sensor-diagnostic-button" :disabled="sensorActionBusy" @click="runSensorDiagnostic">执行传感器检查</button>
            </div>
            <div class="calibration-grid">
              <article v-for="item in sensorCalibrations" :key="item.key" class="calibration-card">
                <div class="calibration-copy">
                  <span class="calibration-icon">{{ item.icon }}</span>
                  <div><b>{{ item.title }}</b><small>{{ item.description }}</small></div>
                </div>
                <div class="calibration-state">
                  <span :class="['calibration-state-dot', calibrationState[item.key]]"></span>
                  <small>{{ calibrationStateText(item.key) }}</small>
                </div>
                <button
                  :disabled="sensorActionBusy || (bridgeMode === 'live' && px4Armed)"
                  @click="calibrateSensor(item.key)"
                >{{ calibrationButtonText(item.key) }}</button>
              </article>
            </div>
            <div class="calibration-note">
              <b>教学说明</b>
              <span v-if="bridgeMode === 'live'">真实 PX4 模式会发送 MAV_CMD_PREFLIGHT_CALIBRATION。加速度计与罗盘校准需要按 PX4 状态提示完成姿态动作；这里不会把“命令已受理”伪装成“校准完成”。</span>
              <span v-else>当前为教学模拟模式。校准流程用于练习判断与操作，不代表真实飞控已写入校准参数。</span>
            </div>
          </section>
        </div>
      </template>

      <template v-else-if="activeSection === 'rc'">
        <div class="rc-workbench">
          <section class="surface rc-summary-surface">
            <div class="rc-summary-main">
              <div>
                <span class="rc-kicker">PX4 RADIO CONTROL WORKBENCH</span>
                <h2>遥控系统 / 通道校准</h2>
                <p>观察接收机原始 PWM，检查 Roll / Pitch / Throttle / Yaw 映射、方向、端点、中位和死区。虚拟遥控只用于教学，不向真实 PX4 发送操纵量。</p>
              </div>
              <div class="rc-summary-score">
                <small>遥控调试得分</small>
                <b :class="{ warn: rcScore < 90 }">{{ rcScore }}<em>/100</em></b>
              </div>
            </div>
            <div class="rc-summary-strip">
              <div><span>输入源</span><b>{{ rcInputSourceText }}</b></div>
              <div><span>接收机链路</span><b :class="rcLinkClass">{{ rcLinkText }}</b></div>
              <div><span>RSSI</span><b>{{ rcRssiText }}</b></div>
              <div><span>待应用参数</span><b :class="{ warn: rcDirtyCount > 0 }">{{ rcDirtyCount }} 项</b></div>
            </div>
            <div v-if="bridgeMode === 'live' && !hasLiveRcInput" class="rc-no-input-banner">
              <span>!</span>
              <div><b>PX4 已连接，但尚未收到 RC_CHANNELS</b><small>SIH 默认可能没有物理接收机输入。可使用下方“虚拟遥控教学输入”练习映射与校准；虚拟输入不会发给 PX4。</small></div>
            </div>
          </section>

          <div class="rc-top-grid">
            <section class="surface rc-stick-surface">
              <div class="surface-heading">
                <div><span class="heading-icon">⌁</span><b>摇杆 / 手动输入监视</b></div>
                <div class="rc-source-actions">
                  <button :class="{ active: rcVirtualMode }" @click="rcVirtualMode = true">虚拟教学输入</button>
                  <button :class="{ active: !rcVirtualMode }" :disabled="!hasLiveRcInput" @click="rcVirtualMode = false">真实 RC 输入</button>
                </div>
              </div>
              <div class="rc-stick-grid">
                <div class="stick-card">
                  <div class="stick-title"><b>Yaw / Throttle</b><small>左摇杆</small></div>
                  <div class="stick-pad">
                    <i class="stick-axis horizontal"></i><i class="stick-axis vertical"></i>
                    <span class="stick-dot" :style="leftStickStyle"></span>
                    <small class="stick-top">THR {{ formatRcPercent(rcMappedValues.throttle) }}</small>
                    <small class="stick-bottom">YAW {{ formatRcSigned(rcMappedValues.yaw) }}</small>
                  </div>
                </div>
                <div class="stick-card">
                  <div class="stick-title"><b>Roll / Pitch</b><small>右摇杆</small></div>
                  <div class="stick-pad">
                    <i class="stick-axis horizontal"></i><i class="stick-axis vertical"></i>
                    <span class="stick-dot" :style="rightStickStyle"></span>
                    <small class="stick-top">PITCH {{ formatRcSigned(rcMappedValues.pitch) }}</small>
                    <small class="stick-bottom">ROLL {{ formatRcSigned(rcMappedValues.roll) }}</small>
                  </div>
                </div>
              </div>
              <div v-if="rcVirtualMode" class="virtual-rc-controls">
                <label v-for="channel in [1,2,3,4]" :key="channel">
                  <span>CH{{ channel }}</span>
                  <input
                    :value="rcDemoChannels[channel - 1]"
                    type="range"
                    min="900"
                    max="2100"
                    step="1"
                    @input="setDemoRcChannel(channel - 1, $event)"
                  />
                  <b>{{ rcDemoChannels[channel - 1] }} μs</b>
                </label>
                <button @click="resetVirtualRc">摇杆回中 / 油门最低</button>
              </div>
              <div class="rc-manual-note">
                <b>安全边界</b><span>虚拟摇杆只改变网页教学数据，不调用 MANUAL_CONTROL 或 RC_OVERRIDE，不会控制真实飞机。</span>
              </div>
            </section>

            <section class="surface rc-channel-surface">
              <div class="surface-heading">
                <div><span class="heading-icon">▤</span><b>接收机通道实时值</b></div>
                <span class="heading-note">{{ rcChannelAgeText }}</span>
              </div>
              <div class="rc-channel-list">
                <div v-for="channel in rcVisibleChannels" :key="channel" class="rc-channel-row">
                  <div class="rc-channel-name">
                    <b>CH{{ channel }}</b>
                    <small>{{ rcChannelRoles(channel) }}</small>
                  </div>
                  <div class="rc-channel-bar"><i :style="{ width: rcChannelBarPercent(channel) }"></i><span class="center-mark"></span></div>
                  <strong>{{ rcChannelValue(channel) }}</strong>
                </div>
              </div>
            </section>
          </div>

          <div class="rc-config-grid">
            <section class="surface rc-mapping-surface">
              <div class="surface-heading">
                <div><span class="heading-icon">⚙</span><b>主控制通道映射与校准</b></div>
                <span class="heading-note">RC_MAP_* / RCx_MIN·TRIM·MAX·REV</span>
              </div>
              <div class="rc-param-compat-note">
                <b>PX4 main 兼容</b><span>每通道 Min/Trim/Max/Reverse 可写入 PX4；“教学死区”仅用于网页归一化演示，不写入飞控。PX4 当前使用 MAN_DEADZONE 等手动控制参数处理特定场景的死区。</span>
              </div>
              <div class="rc-role-table">
                <div class="rc-role-head"><span>功能</span><span>映射通道</span><span>Min</span><span>Trim</span><span>Max</span><span>方向</span><span>教学死区</span><span>实时</span></div>
                <div v-for="role in rcRoles" :key="role" class="rc-role-row">
                  <div><b>{{ rcRoleLabels[role] }}</b><code>{{ rcMapParams[role] }}</code></div>
                  <select v-model.number="rcDraft.mapping[role]" @change="ensureRcCalibration(rcDraft.mapping[role])">
                    <option v-for="channel in rcChannelOptions" :key="channel" :value="channel">{{ channel === 0 ? '未分配' : `CH${channel}` }}</option>
                  </select>
                  <input v-model.number="rcDraft.channels[rcDraft.mapping[role]].min" type="number" min="800" max="1500" step="1" />
                  <input v-model.number="rcDraft.channels[rcDraft.mapping[role]].trim" type="number" min="800" max="2200" step="1" />
                  <input v-model.number="rcDraft.channels[rcDraft.mapping[role]].max" type="number" min="1500" max="2200" step="1" />
                  <select v-model.number="rcDraft.channels[rcDraft.mapping[role]].reverse"><option :value="1">正常</option><option :value="-1">反向</option></select>
                  <input v-model.number="rcDraft.channels[rcDraft.mapping[role]].deadzone" type="number" min="0" max="100" step="1" />
                  <div class="rc-normalized"><i :style="{ width: rcRoleMeterWidth(role) }"></i><b>{{ role === 'throttle' ? formatRcPercent(rcMappedValues[role]) : formatRcSigned(rcMappedValues[role]) }}</b></div>
                </div>
              </div>
            </section>

            <section class="surface rc-calibration-surface">
              <div class="surface-heading">
                <div><span class="heading-icon">◎</span><b>行程采集与调试检查</b></div>
                <span :class="['rc-check-pill', rcValidationErrors.length ? 'warn' : 'ok']">{{ rcValidationErrors.length ? '存在错误' : '参数可用' }}</span>
              </div>
              <div class="rc-capture-panel">
                <div class="capture-copy">
                  <b>{{ rcCaptureActive ? '正在采集摇杆行程…' : rcCaptureComplete ? '本次行程采集已完成' : '尚未进行本次行程采集' }}</b>
                  <small>开始后将四个主摇杆缓慢移动到所有端点，再回到中位；停止时只更新本地草稿，不会立即写入 PX4。</small>
                </div>
                <div class="capture-actions">
                  <button v-if="!rcCaptureActive" @click="startRcCapture">开始行程采集</button>
                  <button v-else class="capture-stop" @click="finishRcCapture">停止并写入草稿</button>
                  <button :disabled="rcCaptureActive" @click="captureRcCenters">采集当前中位</button>
                </div>
                <div class="capture-ranges">
                  <div v-for="role in rcRoles" :key="role"><span>{{ rcRoleLabels[role] }}</span><b>{{ rcObservedRangeText(role) }}</b></div>
                </div>
              </div>

              <div class="rc-issue-list">
                <div v-if="rcValidationIssues.length === 0" class="rc-no-issues"><span>✓</span><div><b>映射与校准参数未发现明显冲突</b><small>继续用摇杆实时值检查方向和端点是否符合预期。</small></div></div>
                <div v-for="issue in rcValidationIssues" :key="issue.code" :class="['rc-issue', issue.level]"><span>{{ issue.level === 'error' ? '!' : '△' }}</span><div><b>{{ issue.title }}</b><small>{{ issue.detail }}</small></div></div>
              </div>

              <div class="rc-actions">
                <button :disabled="rcBusy" @click="loadRcParameters">{{ bridgeMode === 'live' ? '从 PX4 读取' : '恢复教学初始值' }}</button>
                <button :disabled="rcBusy" @click="loadRecommendedRcProfile">载入推荐校准</button>
                <button class="primary-action" :disabled="rcBusy || px4Armed || rcValidationErrors.length > 0 || rcDirtyCount === 0" @click="applyRcParameters">{{ bridgeMode === 'live' ? `应用 ${rcDirtyCount} 项到 PX4` : '应用模拟参数' }}</button>
                <button class="verify-action" :disabled="rcBusy" @click="verifyRcSystem">运行遥控系统检查</button>
              </div>
              <div v-if="rcMessage" :class="['rc-message', rcMessageLevel]">{{ rcMessage }}</div>
            </section>
          </div>

          <section class="surface rc-failsafe-surface">
            <div class="surface-heading"><div><span class="heading-icon">◇</span><b>链路丢失 / Failsafe 联动</b></div><button class="link-safety-button" @click="activeSection = 'safety'">前往安全设置</button></div>
            <div class="rc-failsafe-grid">
              <div><span>RC Loss Timeout</span><b>{{ Number(safetyDraft.COM_RC_LOSS_T).toFixed(1) }} s</b><code>COM_RC_LOSS_T</code></div>
              <div><span>RC Loss Action</span><b>{{ rcLossActionText }}</b><code>NAV_RCL_ACT</code></div>
              <div><span>输入数据年龄</span><b :class="rcInputStale ? 'warn-text' : 'ok-text'">{{ rcChannelAgeText }}</b><small>超过失联时间时应由 PX4 Failsafe 接管，而不是网页自行决定。</small></div>
            </div>
          </section>
        </div>
      </template>

      <template v-else-if="activeSection === 'power'">
        <div class="power-layout">
          <section class="surface scene-surface">
            <div class="surface-heading">
              <div>
                <span class="heading-icon">▣</span>
                <b>四旋翼无人机 3D 视图</b>
              </div>
              <span class="heading-note">当前飞机：{{ assemblyStore.aircraftName }}</span>
            </div>

            <div class="scene-and-controls">
              <DebugMotorScene
                :telemetry="debugTelemetry"
                :aircraft="assemblyStore.aircraft"
                :components="assemblyStore.components"
                :engineering="assemblyStore.engineering"
                :commanded-motor="commandedMotor"
                :actual-motor="actualMotor"
                :fault-motor="faultMotor"
                :live="bridgeMode === 'live'"
              />

              <div class="motor-test-stack">
                <button
                  v-for="motor in motorNames"
                  :key="motor"
                  :class="['motor-test', { active: commandedMotor === motor }]"
                  :disabled="motorTestBusy"
                  @click="testMotor(motor)"
                >
                  <span>▶</span> 测试 {{ motor }}
                </button>
                <button class="stop-all" @click="stopAllMotors"><span>■</span> 全部停止</button>
              </div>
            </div>
          </section>

          <section class="surface parameter-surface">
            <div class="surface-heading">
              <div><span class="heading-icon">▤</span><b>动力系统参数</b></div>
            </div>
            <div class="metric-grid">
              <div class="metric-card"><span>▥</span><small>电池</small><b>{{ batteryText }}</b></div>
              <div class="metric-card"><span>▥</span><small>推重比</small><b>{{ thrustRatioText }}</b></div>
              <div class="metric-card"><span>◔</span><small>悬停油门</small><b>{{ hoverThrottleText }}</b></div>
              <div class="metric-card"><span>ϟ</span><small>最大电流</small><b>{{ maxCurrentText }}</b></div>
              <div class="metric-card good"><span>✓</span><small>ESC 裕量</small><b>{{ escMarginText }}</b></div>
              <div class="metric-card good"><span>♡</span><small>电池状态</small><b>{{ batteryHealthText }}</b></div>
            </div>
            <div class="safety-tip">ⓘ 教学演示模式仅驱动数字旋翼；接入 PX4 后再发送真实执行机构测试指令。</div>
          </section>
        </div>

        <div class="lower-grid">
          <section class="surface actuator-surface">
            <div class="surface-heading"><div><span class="heading-icon">⚙</span><b>执行机构状态</b></div></div>
            <div class="actuator-list">
              <div v-for="(motor, index) in motorNames" :key="motor" class="actuator-row">
                <b>{{ motor }}</b><span>输出</span>
                <div class="output-bar"><i :style="{ width: `${Math.round(motorOutputs[index] * 100)}%` }"></i></div>
                <strong>{{ Math.round(motorOutputs[index] * 100) }}%</strong>
              </div>
            </div>
          </section>

          <section class="surface mapping-surface">
            <div class="surface-heading"><div><span class="heading-icon">⚙</span><b>旋向与映射</b></div></div>
            <table>
              <thead><tr><th>电机</th><th>位置</th><th>理论旋向</th><th>当前响应</th></tr></thead>
              <tbody>
                <tr v-for="row in motorRows" :key="row.motor">
                  <td>{{ row.motor }}</td><td>{{ row.position }}</td><td>{{ row.direction }}</td>
                  <td :class="row.responseClass">{{ row.response }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="mappingFaultVisible" class="fault-banner">
              <span>!</span>
              <div>
                <b>检测到：M1 指令触发后实际 M3 响应</b>
                <small>疑似执行机构映射错误。可在教学场景中执行修复。</small>
              </div>
              <button @click="repairMotorMapping">修复映射</button>
            </div>
            <div v-else class="pass-banner"><span>✓</span> 电机响应与理论映射一致</div>
          </section>
        </div>
      </template>


      <template v-else-if="activeSection === 'safety'">
        <div class="safety-workbench">
          <section class="surface safety-summary-surface">
            <div class="safety-summary-main">
              <div>
                <span class="safety-kicker">PX4 SAFETY CONFIGURATION</span>
                <h2>安全设置与 Failsafe 策略</h2>
                <p>读取并编辑 PX4 安全参数，先在本地草稿中完成策略检查，再统一写入飞控。教学模拟模式不会伪装成真实 PX4 写入。</p>
              </div>
              <div class="safety-summary-score">
                <small>安全配置得分</small>
                <b :class="{ warn: safetyScore < 90 }">{{ safetyScore }}<em>/100</em></b>
              </div>
            </div>
            <div class="safety-summary-strip">
              <div><span>参数源</span><b>{{ bridgeMode === 'live' ? 'PX4 实时参数' : '教学模拟' }}</b></div>
              <div><span>待应用</span><b :class="{ warn: safetyDirtyCount > 0 }">{{ safetyDirtyCount }} 项</b></div>
              <div><span>配置检查</span><b :class="safetyValidationIssues.length ? 'warn' : 'ok'">{{ safetyValidationIssues.length ? `${safetyValidationIssues.length} 项提醒` : '通过' }}</b></div>
              <div><span>飞控状态</span><b :class="px4Armed ? 'bad' : 'ok'">{{ px4Armed ? '已解锁 · 禁止写入' : '未解锁' }}</b></div>
            </div>
            <div v-if="scenario === 'failsafe' && bridgeMode !== 'live'" class="safety-training-banner" :class="{ repaired: demoFailsafeRepaired }">
              <span>{{ demoFailsafeRepaired ? '✓' : '!' }}</span>
              <div>
                <b>{{ demoFailsafeRepaired ? 'Failsafe 教学故障已修复' : '训练场景：Failsafe 配置异常' }}</b>
                <small>{{ demoFailsafeRepaired ? '当前草稿已恢复到教学推荐策略，可继续进行 Pre-Arm 检查。' : '当前模拟配置包含失控保护禁用、低电量仅告警等风险项，请完成诊断并修复。' }}</small>
              </div>
            </div>
          </section>

          <div class="safety-card-grid">
            <section class="surface safety-config-card">
              <div class="surface-heading">
                <div><span class="heading-icon">⌁</span><b>遥控 / 数据链路失联保护</b></div>
                <span class="heading-note">RC & Data Link Loss</span>
              </div>
              <div class="safety-fields">
                <label class="safety-field">
                  <div><b>遥控失联判定时间</b><code>COM_RC_LOSS_T</code><small>最后一次有效手动控制输入之后，多久判定为失联。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.COM_RC_LOSS_T" type="number" min="0" max="35" step="0.1" @input="markSafetyDirty('COM_RC_LOSS_T')" /><span>s</span></div>
                </label>
                <label class="safety-field">
                  <div><b>遥控失联动作</b><code>NAV_RCL_ACT</code><small>教学页默认推荐 Return；危险的终止/空中上锁动作不提供快捷选择。</small></div>
                  <select v-model.number="safetyDraft.NAV_RCL_ACT" @change="markSafetyDirty('NAV_RCL_ACT')">
                    <option :value="0">禁用</option><option :value="1">Hold 悬停</option><option :value="2">Return 返航</option><option :value="3">Land 降落</option>
                    <option :value="5" disabled>Terminate（危险）</option><option :value="6" disabled>Disarm（危险）</option><option :value="7">Hold（无 Failsafe 状态）</option>
                  </select>
                </label>
                <label class="safety-field">
                  <div><b>故障响应延时</b><code>COM_FAIL_ACT_T</code><small>触发后先进入 Hold，等待链路恢复，再执行配置的保护动作。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.COM_FAIL_ACT_T" type="number" min="0" max="25" step="0.5" @input="markSafetyDirty('COM_FAIL_ACT_T')" /><span>s</span></div>
                </label>
                <label class="safety-field">
                  <div><b>地面站链路失联时间</b><code>COM_DL_LOSS_T</code><small>MAVLink 地面站连接中断达到该时长后触发数据链路保护。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.COM_DL_LOSS_T" type="number" min="5" max="300" step="1" @input="markSafetyDirty('COM_DL_LOSS_T')" /><span>s</span></div>
                </label>
                <label class="safety-field">
                  <div><b>数据链路失联动作</b><code>NAV_DLL_ACT</code><small>建议教学训练使用 Return 或 Hold，避免直接终止飞行。</small></div>
                  <select v-model.number="safetyDraft.NAV_DLL_ACT" @change="markSafetyDirty('NAV_DLL_ACT')">
                    <option :value="0">禁用</option><option :value="1">Hold 悬停</option><option :value="2">Return 返航</option><option :value="3">Land 降落</option>
                    <option :value="5" disabled>Terminate（危险）</option><option :value="6" disabled>Disarm（危险）</option>
                  </select>
                </label>
              </div>
            </section>

            <section class="surface safety-config-card">
              <div class="surface-heading">
                <div><span class="heading-icon">▰</span><b>低电量保护</b></div>
                <span class="heading-note">Battery Failsafe</span>
              </div>
              <div class="battery-threshold-visual">
                <div class="battery-scale"><i class="low" :style="{ left: safetyPercent(safetyDraft.BAT_LOW_THR) }"></i><i class="critical" :style="{ left: safetyPercent(safetyDraft.BAT_CRIT_THR) }"></i><i class="emergency" :style="{ left: safetyPercent(safetyDraft.BAT_EMERGEN_THR) }"></i></div>
                <div class="battery-scale-labels"><span>0%</span><span>剩余电量阈值</span><span>50%</span></div>
              </div>
              <div class="safety-fields">
                <label class="safety-field">
                  <div><b>低电量告警阈值</b><code>BAT_LOW_THR</code><small>必须高于 Critical 与 Emergency 阈值。</small></div>
                  <div class="safety-input"><input :value="safetyPctValue('BAT_LOW_THR')" type="number" min="0" max="50" step="1" @input="setSafetyPercent('BAT_LOW_THR', $event)" /><span>%</span></div>
                </label>
                <label class="safety-field">
                  <div><b>严重低电量阈值</b><code>BAT_CRIT_THR</code><small>通常在此阶段执行返航等保护动作。</small></div>
                  <div class="safety-input"><input :value="safetyPctValue('BAT_CRIT_THR')" type="number" min="0" max="50" step="1" @input="setSafetyPercent('BAT_CRIT_THR', $event)" /><span>%</span></div>
                </label>
                <label class="safety-field">
                  <div><b>紧急电量阈值</b><code>BAT_EMERGEN_THR</code><small>应低于 Critical，通常用于紧急降落阶段。</small></div>
                  <div class="safety-input"><input :value="safetyPctValue('BAT_EMERGEN_THR')" type="number" min="0" max="50" step="1" @input="setSafetyPercent('BAT_EMERGEN_THR', $event)" /><span>%</span></div>
                </label>
                <label class="safety-field">
                  <div><b>低电量保护策略</b><code>COM_LOW_BAT_ACT</code><small>教学推荐：Critical 时返航、Emergency 时降落。</small></div>
                  <select v-model.number="safetyDraft.COM_LOW_BAT_ACT" @change="markSafetyDirty('COM_LOW_BAT_ACT')">
                    <option :value="0">仅告警</option><option :value="2">Land 降落</option><option :value="3">Return → Land</option><option :value="4" disabled>Return → Terminate（危险）</option>
                  </select>
                </label>
                <label class="safety-field">
                  <div><b>最低解锁电量</b><code>COM_ARM_BAT_MIN</code><small>低于该剩余电量时禁止解锁；0 表示关闭此检查。</small></div>
                  <div class="safety-input"><input :value="safetyPctValue('COM_ARM_BAT_MIN')" type="number" min="0" max="90" step="1" @input="setSafetyPercent('COM_ARM_BAT_MIN', $event)" /><span>%</span></div>
                </label>
              </div>
            </section>

            <section class="surface safety-config-card">
              <div class="surface-heading">
                <div><span class="heading-icon">⌖</span><b>返航 / 地理围栏</b></div>
                <span class="heading-note">RTL & Geofence</span>
              </div>
              <div class="geofence-preview">
                <div class="geofence-cylinder">
                  <span class="gf-drone">✤</span>
                  <i></i>
                </div>
                <div><span>水平半径</span><b>{{ safetyDraft.GF_MAX_HOR_DIST }} m</b><span>高度</span><b>{{ safetyDraft.GF_MAX_VER_DIST }} m</b></div>
              </div>
              <div class="safety-fields">
                <label class="safety-field">
                  <div><b>返航高度</b><code>RTL_RETURN_ALT</code><small>若当前高度低于此值，Return 时先爬升到该高度。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.RTL_RETURN_ALT" type="number" min="2" max="300" step="1" @input="markSafetyDirty('RTL_RETURN_ALT')" /><span>m</span></div>
                </label>
                <label class="safety-field">
                  <div><b>围栏水平半径</b><code>GF_MAX_HOR_DIST</code><small>以 Home 为中心的最大水平距离；0 表示关闭此限制。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.GF_MAX_HOR_DIST" type="number" min="0" max="10000" step="1" @input="markSafetyDirty('GF_MAX_HOR_DIST')" /><span>m</span></div>
                </label>
                <label class="safety-field">
                  <div><b>围栏垂直高度</b><code>GF_MAX_VER_DIST</code><small>相对 Home 的最大垂直距离；0 表示关闭此限制。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.GF_MAX_VER_DIST" type="number" min="0" max="10000" step="1" @input="markSafetyDirty('GF_MAX_VER_DIST')" /><span>m</span></div>
                </label>
                <label class="safety-field">
                  <div><b>越界动作</b><code>GF_ACTION</code><small>PX4 文档建议严格围栏场景优先采用 Hold 并留出制动距离。</small></div>
                  <select v-model.number="safetyDraft.GF_ACTION" @change="markSafetyDirty('GF_ACTION')">
                    <option :value="0">None</option><option :value="1">Warning</option><option :value="2">Hold</option><option :value="3">Return</option><option :value="5">Land</option><option :value="4" disabled>Terminate（危险）</option>
                  </select>
                </label>
              </div>
            </section>

            <section class="surface safety-config-card">
              <div class="surface-heading">
                <div><span class="heading-icon">◇</span><b>解锁 / 自动上锁条件</b></div>
                <span class="heading-note">Arming Safety</span>
              </div>
              <div class="arming-gate">
                <div :class="['arming-gate-icon', prearmPassed ? 'pass' : 'block']">{{ prearmPassed ? '✓' : '×' }}</div>
                <div><b>{{ prearmPassed ? '当前 Pre-Arm 未发现阻断' : '当前存在 Pre-Arm 阻断或待检查项' }}</b><small>{{ prearmMessage }}</small></div>
              </div>
              <div class="safety-fields">
                <label class="safety-field">
                  <div><b>允许解锁</b><code>COM_ARMABLE</code><small>维护或检修状态可临时关闭解锁能力。</small></div>
                  <select v-model.number="safetyDraft.COM_ARMABLE" @change="markSafetyDirty('COM_ARMABLE')"><option :value="1">允许</option><option :value="0">禁止</option></select>
                </label>
                <label class="safety-field">
                  <div><b>无 GPS 是否允许解锁</b><code>COM_ARM_WO_GPS</code><small>教学飞行验证建议要求 GPS/位置条件满足后再解锁。</small></div>
                  <select v-model.number="safetyDraft.COM_ARM_WO_GPS" @change="markSafetyDirty('COM_ARM_WO_GPS')"><option :value="0">要求 GPS</option><option :value="1">允许无 GPS</option></select>
                </label>
                <label class="safety-field">
                  <div><b>起飞前自动上锁</b><code>COM_DISARM_PRFLT</code><small>解锁后未及时起飞，超过该时间自动重新上锁。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.COM_DISARM_PRFLT" type="number" min="-1" max="120" step="1" @input="markSafetyDirty('COM_DISARM_PRFLT')" /><span>s</span></div>
                </label>
                <label class="safety-field">
                  <div><b>落地后自动上锁</b><code>COM_DISARM_LAND</code><small>检测到落地后持续该时间，PX4 自动上锁电机。</small></div>
                  <div class="safety-input"><input v-model.number="safetyDraft.COM_DISARM_LAND" type="number" min="0" max="120" step="0.5" @input="markSafetyDirty('COM_DISARM_LAND')" /><span>s</span></div>
                </label>
              </div>
            </section>
          </div>

          <section class="surface safety-diagnostic-surface">
            <div class="surface-heading">
              <div><span class="heading-icon">☑</span><b>安全策略检查</b></div>
              <span :class="['safety-check-pill', safetyValidationIssues.length ? 'warn' : 'ok']">{{ safetyValidationIssues.length ? '需要处理' : '配置合理' }}</span>
            </div>
            <div class="safety-diagnostic-body">
              <div class="safety-issue-list">
                <div v-if="safetyValidationIssues.length === 0" class="safety-no-issues"><span>✓</span><div><b>未发现明显配置冲突</b><small>仍需结合具体机型、场地和课程任务进行人工复核。</small></div></div>
                <div v-for="issue in safetyValidationIssues" :key="issue.code" :class="['safety-issue', issue.level]">
                  <span>{{ issue.level === 'error' ? '!' : '△' }}</span>
                  <div><b>{{ issue.title }}</b><small>{{ issue.detail }}</small></div>
                </div>
              </div>
              <div class="safety-actions">
                <button :disabled="safetyBusy" @click="loadSafetyParameters">{{ bridgeMode === 'live' ? '从 PX4 重新读取' : '恢复模拟初始值' }}</button>
                <button :disabled="safetyBusy" @click="loadRecommendedSafetyProfile">载入教学推荐值</button>
                <button class="primary-action" :disabled="safetyBusy || px4Armed || safetyValidationErrors.length > 0 || safetyDirtyCount === 0" @click="applySafetyParameters">
                  {{ bridgeMode === 'live' ? `应用 ${safetyDirtyCount} 项到 PX4` : '应用模拟配置' }}
                </button>
                <button class="verify-action" :disabled="safetyBusy" @click="verifySafetyConfiguration">运行安全 / Pre-Arm 验证</button>
              </div>
            </div>
            <div v-if="safetyMessage" :class="['safety-message', safetyMessageLevel]">{{ safetyMessage }}</div>
          </section>
        </div>
      </template>

      <template v-else-if="activeSection === 'preflight'">
        <div class="preflight-workbench">
          <section class="surface preflight-hero" :class="{ ready: preflightReady, blocked: !preflightReady }">
            <div class="preflight-hero-copy">
              <span class="preflight-kicker">FINAL PRE-FLIGHT GATE</span>
              <h2>起飞前检查与飞行许可</h2>
              <p>汇总装配、传感器、遥控、动力、安全设置与 PX4 Pre-Arm 结果。所有阻断项处理完成并执行最终检查后，才生成本架飞机的飞行许可。</p>
            </div>
            <div class="preflight-permit">
              <span :class="['permit-ring', preflightReady ? 'pass' : 'block']">{{ preflightReady ? '✓' : '!' }}</span>
              <div><small>当前状态</small><b>{{ preflightReady ? '满足起飞条件' : `存在 ${preflightBlockers.length} 项阻断` }}</b></div>
              <strong>{{ preflightScoreValue }}<em>/100</em></strong>
            </div>
          </section>

          <section class="surface preflight-check-surface">
            <div class="surface-heading">
              <div><span class="heading-icon">☑</span><b>六项起飞门禁</b></div>
              <span :class="['preflight-count-pill', preflightReady ? 'ok' : 'warn']">{{ preflightPassedCount }}/{{ preflightChecks.length }} 通过</span>
            </div>
            <div class="preflight-check-grid">
              <article v-for="item in preflightChecks" :key="item.key" :class="['preflight-check-card', item.state]">
                <div class="check-state-icon">{{ item.state === 'pass' ? '✓' : item.state === 'warn' ? '△' : '×' }}</div>
                <div class="check-copy">
                  <span>{{ item.title }}</span>
                  <b>{{ item.summary }}</b>
                  <small>{{ item.detail }}</small>
                </div>
                <button v-if="item.section" @click="activeSection = item.section">检查</button>
              </article>
            </div>
          </section>

          <div class="preflight-lower-grid">
            <section class="surface preflight-aircraft-summary">
              <div class="surface-heading"><div><span class="heading-icon">◇</span><b>飞机与工程快照</b></div></div>
              <dl>
                <div><dt>飞机</dt><dd>{{ assemblyStore.aircraftName }}</dd></div>
                <div><dt>飞机 ID</dt><dd>{{ assemblyStore.activeAircraftId ?? '—' }}</dd></div>
                <div><dt>总质量</dt><dd>{{ massKg.toFixed(3) }} kg</dd></div>
                <div><dt>推重比</dt><dd>{{ thrustRatioText }}</dd></div>
                <div><dt>桥接模式</dt><dd>{{ bridgeMode === 'live' ? 'PX4 SIH / MAVLink' : '教学模拟' }}</dd></div>
                <div><dt>训练场景</dt><dd>{{ scenarios.find(item => item.key === scenario)?.title }}</dd></div>
              </dl>
            </section>

            <section class="surface preflight-blocker-surface">
              <div class="surface-heading"><div><span class="heading-icon">!</span><b>阻断项 / 提醒</b></div></div>
              <div v-if="preflightBlockers.length === 0 && preflightWarnings.length === 0" class="preflight-clear">
                <span>✓</span><div><b>未发现阻断项</b><small>可以执行最终检查并生成飞行许可。</small></div>
              </div>
              <div v-for="item in preflightBlockers" :key="`block-${item.key}`" class="preflight-issue block"><span>×</span><div><b>{{ item.title }}</b><small>{{ item.summary }}</small></div></div>
              <div v-for="item in preflightWarnings" :key="`warn-${item.key}`" class="preflight-issue warn"><span>△</span><div><b>{{ item.title }}</b><small>{{ item.summary }}</small></div></div>
            </section>
          </div>

          <section class="surface preflight-final-surface">
            <div class="preflight-final-copy">
              <b>{{ preflightPermitValid ? '飞行许可已生成' : '尚未生成飞行许可' }}</b>
              <small v-if="preflightPermitValid">检查时间：{{ preflightSavedAtText }}。许可仅对当前飞机配置有效，配置变化或超过 1 小时后自动失效。</small>
              <small v-else>{{ preflightMessage || '先完成六项门禁，再执行最终检查。' }}</small>
            </div>
            <div class="preflight-final-actions">
              <button :disabled="preflightBusy" @click="runFinalPreflight">{{ preflightBusy ? '检查中…' : '执行最终起飞检查' }}</button>
              <RouterLink v-if="preflightPermitValid" class="preflight-flight-button" :to="flightRoute">进入飞行验证</RouterLink>
              <button v-else class="preflight-flight-button disabled" disabled>进入飞行验证</button>
            </div>
          </section>
        </div>
      </template>
    </main>

    <aside class="debug-rightbar">
      <section class="surface telemetry-surface">
        <div class="surface-heading"><div><span class="heading-icon">▥</span><b>实时状态 / 遥测</b></div></div>
        <div class="status-grid">
          <div><span>飞控</span><b>{{ bridgeMode === 'live' ? 'PX4 SIH' : '教学模拟' }}</b></div>
          <div><span>电池</span><b>{{ batteryVoltageText }}</b></div>
          <div><span>模式</span><b class="standby">{{ px4ModeText }}</b></div>
          <div><span>EKF</span><b :class="ekfOk ? 'ok' : 'warn'">{{ ekfText }}</b></div>
          <div><span>GPS</span><b :class="gpsHealthy ? 'ok' : 'warn'">{{ gpsStatus }}</b></div>
          <div><span>Arming</span><b :class="px4Armed ? 'ok' : 'bad'">{{ px4Armed ? '已解锁' : '未解锁' }}</b></div>
          <div><span>高度</span><b>{{ liveAltitudeText }}</b></div>
          <div><span>Bridge</span><b :class="bridgeMode === 'live' ? 'ok' : 'warn'">{{ bridgeMode === 'live' ? '在线' : '待连接' }}</b></div>
        </div>
        <div :class="['prearm-alert', { passed: prearmPassed }]">
          <span>!</span>
          <div><b>Pre-Arm Check {{ prearmPassed ? 'Passed' : 'Failed' }}</b><small>{{ prearmMessage }}</small></div>
        </div>
      </section>

      <section class="surface bridge-surface">
        <div class="bridge-row">
          <span class="dot" :class="bridgeMode === 'live' ? 'online' : 'demo'"></span>
          <div><b>PX4 SIH</b><small>{{ bridgeDetailText }}</small></div>
          <strong>{{ bridgeMode === 'live' ? '已连接' : '等待' }}</strong>
        </div>
        <div v-if="bridgeError" class="bridge-error">{{ bridgeError }}</div>
        <div class="bridge-controls">
          <button :disabled="bridgeBusy" @click="connectPx4">连接 PX4</button>
          <button :disabled="bridgeBusy || bridgeMode !== 'live'" @click="runPrearmPx4">Pre-Arm</button>
          <button :disabled="bridgeBusy || bridgeMode !== 'live' || px4Armed" @click="armPx4">解锁</button>
          <button :disabled="bridgeBusy || bridgeMode !== 'live' || !px4Armed" @click="disarmPx4">上锁</button>
          <button :disabled="bridgeBusy || bridgeMode !== 'live' || !px4Armed" @click="takeoffPx4">起飞 2m</button>
          <button :disabled="bridgeBusy || bridgeMode !== 'live'" @click="landPx4">降落</button>
        </div>
        <div class="param-tool">
          <div class="param-row">
            <input v-model.trim="paramName" maxlength="16" placeholder="PX4 参数，如 RTL_RETURN_ALT" />
            <input v-model.number="paramValue" type="number" step="0.01" placeholder="值" />
          </div>
          <div class="param-actions">
            <button :disabled="bridgeMode !== 'live' || bridgeBusy || !paramName" @click="readPx4Parameter">读取参数</button>
            <button :disabled="bridgeMode !== 'live' || bridgeBusy || !paramName || paramValue === null" @click="writePx4Parameter">写入参数</button>
          </div>
          <small v-if="paramMessage">{{ paramMessage }}</small>
        </div>
        <div class="bridge-row secondary">
          <span class="dot demo"></span>
          <div><b>Gazebo</b><small>本阶段不接入；3D 继续使用 UAV-Studio Three.js</small></div>
          <strong>停用</strong>
        </div>
      </section>

      <section class="surface log-surface">
        <div class="surface-heading">
          <div><span class="heading-icon">▤</span><b>调试记录</b></div>
          <button class="clear-log" @click="logs = []">清空记录</button>
        </div>
        <div class="timeline">
          <div v-for="item in logs" :key="item.id" :class="['log-item', item.level]">
            <span class="timeline-dot"></span>
            <time>{{ item.time }}</time>
            <div><b>{{ item.title }}</b><small>{{ item.detail }}</small></div>
          </div>
          <div v-if="logs.length === 0" class="empty-log">尚无调试记录</div>
        </div>
      </section>

      <section class="surface score-surface">
        <span class="trophy">♛</span>
        <div><small>当前调试得分</small><b>{{ score }}<em>/100</em></b></div>
        <div class="remaining"><span>未完成项：</span><b>{{ remainingTasks }}</b></div>
      </section>

      <div class="right-actions">
        <button @click="saveDebugReport">▣ 保存调试记录</button>
        <RouterLink v-if="preflightPermitValid" class="flight-action" :to="flightRoute">➤ 进入飞行验证</RouterLink>
        <button v-else class="flight-action disabled" disabled title="请先完成起飞前检查">➤ 进入飞行验证</button>
      </div>
    </aside>

    <div v-if="trainingLibraryOpen" class="training-library-backdrop" @click.self="trainingLibraryOpen = false">
      <section class="training-library-panel">
        <header>
          <div>
            <span>FAULT TRAINING LIBRARY</span>
            <h2>装调检修故障实训案例库</h2>
            <p>选择案例后回到原调试工作台完成诊断。案例只给出现象和任务，不直接显示故障答案。</p>
          </div>
          <button class="training-close" @click="trainingLibraryOpen = false">×</button>
        </header>
        <div class="training-filter-row">
          <button
            v-for="item in trainingCategoryOptions"
            :key="item.key"
            :class="{ active: trainingCategoryFilter === item.key }"
            @click="trainingCategoryFilter = item.key"
          >{{ item.label }}</button>
        </div>
        <div class="training-case-grid">
          <article v-for="item in filteredTrainingCases" :key="item.id" class="training-case-card">
            <div class="training-case-card-head">
              <span class="training-case-icon">{{ item.icon }}</span>
              <div><small>{{ item.id }} · {{ trainingCategoryLabel(item.category) }}</small><b>{{ item.title }}</b></div>
              <strong>{{ trainingDifficulty(item.difficulty) }}</strong>
            </div>
            <p>{{ item.student_brief.symptom }}</p>
            <dl>
              <div><dt>建议时间</dt><dd>{{ item.recommended_minutes }} min</dd></div>
              <div><dt>故障来源</dt><dd>{{ item.fault_source }}</dd></div>
            </dl>
            <div class="training-case-task"><b>任务</b><span>{{ item.student_brief.task }}</span></div>
            <button class="training-start-button" @click="startTrainingCase(item)">
              {{ activeTrainingCase?.id === item.id ? '重新开始案例' : '开始实训' }}
            </button>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DebugMotorScene from '../components/DebugMotorScene.vue'
import DiagnosisWorksheet, { type DiagnosisWorksheetSnapshot } from '../components/DiagnosisWorksheet.vue'
import { px4Api, type Px4SensorKey, type Px4Telemetry } from '../api/px4'
import { studentTrainingApi } from '../api/teacher'
import { useAssemblyStore } from '../stores/assembly'
import { useAuthStore } from '../stores/auth'
import type { LearningRole } from '../utils/learningGuide'
import type { MotorName } from '../types/aircraft'
import type { MotorVector, TelemetryFrame } from '../types/telemetry'
import { calculateDebugScore, resolveMotorResponse, type DebugScenario } from '../utils/debugging'
import { calculateSafetyScore, recommendedSafetyProfile, safetyParamKeys, unsafeDemoSafetyProfile, validateSafetyDraft, type SafetyDraft, type SafetyParamKey } from '../utils/safety'
import { calculateRcScore, cloneRcDraft, defaultRcDraft, flattenRcDraft, normalizeRcInput, rcMapParams, rcRoleLabels, rcRoles, validateRcDraft, type RcDraft, type RcRole } from '../utils/rc'
import { aircraftFingerprint, clearPreflightSnapshot, loadPreflightSnapshot, preflightScore, savePreflightSnapshot, type PreflightCheckRecord, type PreflightSnapshot } from '../utils/preflight'
import { loadFaultTrainingCases, scoreFaultTraining, trainingCategoryText, trainingDifficultyText, type FaultTrainingCase, type TrainingCategory, type TrainingEvaluation } from '../utils/training'

type SectionKey = 'sensors' | 'rc' | 'power' | 'safety' | 'preflight'
type ScenarioKey = DebugScenario
type LogLevel = 'info' | 'warn' | 'error' | 'success'
type CalibrationState = 'idle' | 'running' | 'requested' | 'passed' | 'failed'
type SensorHealthName = 'gyro' | 'accelerometer' | 'magnetometer' | 'barometer' | 'gps'


interface DebugLog {
  id: number
  time: string
  title: string
  detail: string
  level: LogLevel
}

const assemblyStore = useAssemblyStore()
const auth = useAuthStore()
const route = useRoute()
const activeSection = ref<SectionKey>('power')
const scenario = ref<ScenarioKey>('standard')
const bridgeMode = ref<'demo' | 'live'>('demo')
const bridgeError = ref('')
const bridgeBusy = ref(false)
const liveTelemetry = ref<Px4Telemetry | null>(null)
const requestedStreams = ref(false)
const commandedMotor = ref<MotorName | null>(null)
const actualMotor = ref<MotorName | null>(null)
const mappingRepaired = ref(false)
const motorOutputs = ref<MotorVector>([0, 0, 0, 0])
const motorTestBusy = ref(false)
const clockTick = ref(0)
const logs = ref<DebugLog[]>([])
const paramName = ref('RTL_RETURN_ALT')
const paramValue = ref<number | null>(null)
const paramMessage = ref('')
const sensorActionBusy = ref(false)
const demoCompassRepaired = ref(false)
const calibrationState = ref<Record<Px4SensorKey, CalibrationState>>({
  gyro: 'idle',
  accelerometer: 'idle',
  compass: 'idle',
  barometer: 'idle',
})
const calibrationMessage = ref<Record<Px4SensorKey, string>>({
  gyro: '', accelerometer: '', compass: '', barometer: '',
})

const safetyDraft = ref<SafetyDraft>({ ...unsafeDemoSafetyProfile })
const safetyBaseline = ref<SafetyDraft>({ ...unsafeDemoSafetyProfile })
const safetyDirty = ref<Partial<Record<SafetyParamKey, boolean>>>({})
const safetyBusy = ref(false)
const safetyMessage = ref('')
const safetyMessageLevel = ref<'info' | 'success' | 'warn' | 'error'>('info')
const safetyLoadedOnce = ref(false)
const demoFailsafeRepaired = ref(false)

const rcDraft = ref<RcDraft>(defaultRcDraft(18))
const rcBaselineFlat = ref<Record<string, number>>(flattenRcDraft(rcDraft.value))
const rcBusy = ref(false)
const rcMessage = ref('')
const rcMessageLevel = ref<'info' | 'success' | 'warn' | 'error'>('info')
const rcLoadedOnce = ref(false)
const rcVirtualMode = ref(true)
const rcCaptureActive = ref(false)
const rcCaptureComplete = ref(false)
const rcDemoChannels = ref<number[]>([1500, 1500, 1000, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500])
const rcObservedMin = ref<number[]>(Array(18).fill(Number.POSITIVE_INFINITY))
const rcObservedMax = ref<number[]>(Array(18).fill(Number.NEGATIVE_INFINITY))
let timer: number | undefined
let stopTimer: number | undefined
let px4PollTimer: number | undefined
let pollingPx4 = false
let logId = 0

const sensorVerificationPassed = ref(false)
const rcVerificationPassed = ref(false)
const safetyVerificationPassed = ref(false)
const motorVerified = ref<Record<MotorName, boolean>>({ M1: false, M2: false, M3: false, M4: false })
const preflightBusy = ref(false)
const preflightSnapshot = ref<PreflightSnapshot | null>(null)
const preflightMessage = ref('')

const trainingCases = ref<FaultTrainingCase[]>([])
const trainingCatalogError = ref('')
const trainingLibraryOpen = ref(false)
const trainingCategoryFilter = ref<'all' | TrainingCategory>('all')
const activeTrainingCase = ref<FaultTrainingCase | null>(null)
const trainingStartedAt = ref<number | null>(null)
const trainingFinishedAt = ref<number | null>(null)
const trainingVisitedSections = ref<string[]>([])
const trainingHintsUsed = ref(0)
const trainingWrongOperations = ref(0)
const trainingCurrentHint = ref('')
const trainingSubmittedEvaluation = ref<TrainingEvaluation | null>(null)
const trainingRemoteStatus = ref('')
const diagnosisWorksheetReady = ref(false)
const diagnosisWorksheetSaved = ref(false)
const diagnosisWorksheetRef = ref<{
  isComplete: () => boolean
  save: () => Promise<DiagnosisWorksheetSnapshot>
  getSnapshot: () => DiagnosisWorksheetSnapshot
} | null>(null)
const learningRole = computed<LearningRole>(() => auth.user?.role === 'teacher' || auth.user?.role === 'admin' ? auth.user.role : 'student')
let trainingInternalMutation = false
let trainingSyncTimer: number | undefined
let trainingSyncBusy = false

const trainingCategoryOptions: Array<{ key: 'all' | TrainingCategory; label: string }> = [
  { key: 'all', label: '全部' },
  { key: 'sensors', label: '传感器' },
  { key: 'rc', label: '遥控' },
  { key: 'power', label: '动力' },
  { key: 'safety', label: '安全' },
  { key: 'integrated', label: '综合' },
]

const assignedRunId = computed(() => {
  const raw = Array.isArray(route.query.run) ? route.query.run[0] : route.query.run
  const value = Number(raw)
  return Number.isInteger(value) && value > 0 ? value : null
})
const assignedScenarioId = computed(() => {
  const raw = Array.isArray(route.query.scenario) ? route.query.scenario[0] : route.query.scenario
  return typeof raw === 'string' ? raw : ''
})
const assignedAssignmentId = computed(() => {
  const raw = Array.isArray(route.query.assignment) ? route.query.assignment[0] : route.query.assignment
  const value = Number(raw)
  return Number.isInteger(value) && value > 0 ? value : null
})
const flightRoute = computed(() => assignedRunId.value
  ? {
      path: '/flight',
      query: {
        run: String(assignedRunId.value),
        scenario: assignedScenarioId.value || activeTrainingCase.value?.id || '',
        ...(assignedAssignmentId.value ? { assignment: String(assignedAssignmentId.value) } : {}),
      },
    }
  : '/flight')

const motorNames: MotorName[] = ['M1', 'M2', 'M3', 'M4']
const motorIndex: Record<MotorName, number> = { M1: 0, M2: 1, M3: 2, M4: 3 }
const motorMeta: Record<MotorName, { position: string; direction: string }> = {
  M1: { position: '右前', direction: 'CCW（逆时针）' },
  M2: { position: '右后', direction: 'CW（顺时针）' },
  M3: { position: '左后', direction: 'CCW（逆时针）' },
  M4: { position: '左前', direction: 'CW（顺时针）' },
}

const sensorAxes = ['x', 'y', 'z'] as const
const sensorCalibrations: Array<{ key: Px4SensorKey; icon: string; title: string; description: string }> = [
  { key: 'gyro', icon: '◌', title: '陀螺仪校准', description: '静止放置飞行器，建立角速度零偏基准。' },
  { key: 'accelerometer', icon: '⬡', title: '加速度计六面校准', description: '按六个机体方向依次静止放置，完成姿态基准校准。' },
  { key: 'compass', icon: '◉', title: '磁罗盘校准', description: '按 PX4 提示旋转机体，检查磁场与航向一致性。' },
  { key: 'barometer', icon: '◒', title: '气压计零点校准', description: '执行飞行前地面气压基准校准。' },
]

const steps = [
  { key: 'sensors' as const, icon: '▦', title: '飞控与传感器', subtitle: '检查飞控、IMU、指南针等' },
  { key: 'rc' as const, icon: '⌁', title: '遥控系统', subtitle: '验证遥控器与接收机' },
  { key: 'power' as const, icon: '✤', title: '动力系统', subtitle: '电机 / ESC / 桨叶测试' },
  { key: 'safety' as const, icon: '◇', title: '安全设置', subtitle: 'Failsafe 与安全策略' },
  { key: 'preflight' as const, icon: '☑', title: '起飞前检查', subtitle: '完成整机检查' },
]
const topTabs = steps.slice(0, 4)
const scenarios = [
  { key: 'standard' as const, icon: '◇', title: '标准调试', subtitle: '基础功能调试流程' },
  { key: 'mapping' as const, icon: '△', title: '电机映射故障', subtitle: '教学模拟映射错误' },
  { key: 'compass' as const, icon: '◉', title: '罗盘异常', subtitle: '教学模拟指南针异常' },
  { key: 'failsafe' as const, icon: '⌘', title: 'Failsafe 异常', subtitle: '教学模拟失控保护' },
]

const currentStep = computed(() => steps.find(item => item.key === activeSection.value) ?? steps[2])
const currentModuleDescription = computed(() => ({
  sensors: '用于飞控状态、IMU、磁罗盘、GNSS 与 EKF 的教学化校准和状态观察。PX4 Bridge 已接入时读取真实 MAVLink 状态。',
  rc: '用于通道映射、中位、行程、正反向、链路质量与失控保护的调试。',
  power: '',
  safety: '用于低电量保护、失控保护、返航高度和解锁条件等安全参数教学。',
  preflight: '汇总装配、调试、参数与系统状态，形成进入飞行验证前的最后检查。',
}[activeSection.value]))

const engineering = computed(() => assemblyStore.engineering)
const massKg = computed(() => engineering.value?.total_mass_kg ?? 2.8)
const gravityN = computed(() => massKg.value * 9.80665)
const maxThrustPerMotor = computed(() => engineering.value?.max_thrust_per_motor_n ?? 17.5)
const totalThrustN = computed(() => motorOutputs.value.reduce((sum, item) => sum + item * maxThrustPerMotor.value, 0))
const batteryComponent = computed(() => assemblyStore.componentForSlot('battery'))
const configuredBatteryVoltage = computed(() => {
  const raw = batteryComponent.value?.parameters_json.nominal_voltage_v
  return typeof raw === 'number' ? raw : 22.2
})
const batteryCells = computed(() => {
  const raw = batteryComponent.value?.parameters_json.cell_count
  return typeof raw === 'number' ? raw : 6
})
const batteryText = computed(() => `${batteryCells.value}S / ${configuredBatteryVoltage.value.toFixed(1)}V`)
const batteryVoltageText = computed(() => {
  const live = liveTelemetry.value?.battery.voltage_v
  return bridgeMode.value === 'live' && typeof live === 'number'
    ? `${live.toFixed(1)} V`
    : `${(configuredBatteryVoltage.value + .2).toFixed(1)} V`
})
const thrustRatioText = computed(() => engineering.value ? engineering.value.thrust_weight_ratio.toFixed(2) : '—')
const hoverThrottleText = computed(() => engineering.value ? `${Math.round(engineering.value.hover_throttle * 100)}%` : '—')
const maxCurrentText = computed(() => engineering.value ? `${engineering.value.max_current_a.toFixed(0)}A` : '—')
const escMarginText = computed(() => !engineering.value ? '待计算' : engineering.value.esc_current_margin_a >= 0 ? '通过' : '不足')
const batteryHealthText = computed(() => !engineering.value ? '待计算' : engineering.value.battery_continuous_margin_a >= 0 ? '良好' : '风险')

const px4Armed = computed(() => bridgeMode.value === 'live' ? Boolean(liveTelemetry.value?.armed) : false)
const px4ModeText = computed(() => bridgeMode.value === 'live' ? (liveTelemetry.value?.mode || 'UNKNOWN') : 'STANDBY')
const liveAltitudeText = computed(() => {
  const z = liveTelemetry.value?.local_position.z
  return bridgeMode.value === 'live' && typeof z === 'number' ? `${z.toFixed(2)} m` : '0.00 m'
})
const gpsHealthy = computed(() => bridgeMode.value === 'live'
  ? (liveTelemetry.value?.gps.fix_type ?? 0) >= 3
  : true)
const gpsStatus = computed(() => {
  if (bridgeMode.value === 'live') {
    const gps = liveTelemetry.value?.gps
    const satellites = gps?.satellites
    const fix = gps?.fix_type
    return `${satellites ?? '—'} 星 / Fix ${fix ?? '—'}`
  }
  return scenario.value === 'compass' ? '定位受限' : '7 星'
})
const compassFaultActive = computed(() => (bridgeMode.value === 'demo' || trainingHasInjection('compass_fault')) && scenario.value === 'compass' && !demoCompassRepaired.value)
const ekfOk = computed(() => {
  if (compassFaultActive.value) return false
  if (bridgeMode.value !== 'live') return true
  return liveTelemetry.value?.estimator.ok === true
})
const ekfText = computed(() => {
  if (compassFaultActive.value) return '异常'
  if (bridgeMode.value !== 'live') return '正常'
  if (liveTelemetry.value?.estimator.ok === null || liveTelemetry.value?.estimator.ok === undefined) return '待数据'
  return liveTelemetry.value.estimator.ok ? '正常' : '异常'
})
const bridgeDetailText = computed(() => {
  if (bridgeMode.value === 'live') {
    const age = liveTelemetry.value?.heartbeat_age_s
    return `MAVLink 已连接 · ${liveTelemetry.value?.connection_url ?? '14540'}${typeof age === 'number' ? ` · HB ${age.toFixed(1)}s` : ''}`
  }
  if (bridgeError.value) return bridgeError.value
  return '启动 Bridge 与 PX4 SIH 后点击连接'
})

const mappingFaultVisible = computed(() => (bridgeMode.value === 'demo' || trainingHasInjection('motor_mapping')) && scenario.value === 'mapping' && !mappingRepaired.value)
const faultMotor = computed<MotorName | null>(() => mappingFaultVisible.value ? 'M3' : null)
const prearmPassed = computed(() => {
  if (bridgeMode.value === 'live') return Boolean(liveTelemetry.value?.prearm_ok)
  if (scenario.value === 'mapping') return mappingRepaired.value
  if (scenario.value === 'compass') return demoCompassRepaired.value
  if (scenario.value === 'failsafe') return demoFailsafeRepaired.value
  return true
})
const prearmMessage = computed(() => {
  if (bridgeMode.value === 'live') {
    const text = liveTelemetry.value?.statustext
    if (text) return text
    return prearmPassed.value ? 'PX4 未报告 Pre-Arm 阻断信息。' : '等待 PX4 Pre-Arm 状态。'
  }
  if (scenario.value === 'mapping' && !mappingRepaired.value) return '执行机构映射未通过，请完成 M1–M4 单电机测试。'
  if (scenario.value === 'compass' && !demoCompassRepaired.value) return '磁罗盘/EKF 状态异常，请完成罗盘校准并重新检查。'
  if (scenario.value === 'compass' && demoCompassRepaired.value) return '罗盘教学校准完成，EKF 状态恢复。'
  if (scenario.value === 'failsafe' && !demoFailsafeRepaired.value) return '安全保护参数异常，请检查 Failsafe 设置。'
  if (scenario.value === 'failsafe' && demoFailsafeRepaired.value) return 'Failsafe 教学配置已修复，可继续进行起飞前验证。'
  return '当前教学场景的前置检查已通过。'
})

const score = computed(() => {
  if (bridgeMode.value === 'live') {
    let value = 100
    if (!assemblyStore.validation.passed) value -= 20
    if (!prearmPassed.value) value -= 15
    if (!gpsHealthy.value) value -= 10
    return Math.max(0, value)
  }
  return calculateDebugScore(scenario.value, mappingRepaired.value, assemblyStore.validation.passed, demoCompassRepaired.value, demoFailsafeRepaired.value)
})
const remainingTasks = computed(() => score.value >= 95 ? '起飞前验证' : '故障修复、安全检查')

const safetyDirtyCount = computed(() => safetyParamKeys.filter(key => safetyDirty.value[key]).length)

const safetyValidationIssues = computed(() => validateSafetyDraft(safetyDraft.value))
const safetyValidationErrors = computed(() => safetyValidationIssues.value.filter(issue => issue.level === 'error'))
const safetyScore = computed(() => calculateSafetyScore(
  safetyDraft.value,
  scenario.value === 'failsafe' && !demoFailsafeRepaired.value && bridgeMode.value !== 'live',
))

const engineeringGatePassed = computed(() => Boolean(
  assemblyStore.validation.passed
  && engineering.value
  && engineering.value.thrust_weight_ratio >= 1.2
  && engineering.value.esc_current_margin_a >= 0
  && engineering.value.battery_continuous_margin_a >= 0
))
const allMotorsVerified = computed(() => motorNames.every(motor => motorVerified.value[motor]))
const preflightChecks = computed<Array<PreflightCheckRecord & { detail: string; section?: SectionKey }>>(() => [
  {
    key: 'assembly', title: '数字装配 / 工程校核',
    state: engineeringGatePassed.value ? 'pass' : 'block',
    summary: engineeringGatePassed.value ? '装配与关键工程裕量通过' : '装配或工程裕量存在阻断',
    detail: assemblyStore.validation.passed ? `推重比 ${thrustRatioText.value}，ESC / 电池电流裕量已纳入检查。` : `${assemblyStore.validation.blocking_errors.length} 项装配阻断错误。`,
  },
  {
    key: 'sensors', title: '飞控与传感器', section: 'sensors',
    state: sensorVerificationPassed.value && ekfOk.value && gpsHealthy.value ? 'pass' : 'block',
    summary: sensorVerificationPassed.value ? (ekfOk.value && gpsHealthy.value ? 'IMU / GPS / EKF 检查通过' : '传感器实时状态异常') : '尚未执行传感器系统检查',
    detail: bridgeMode.value === 'live' ? `EKF ${ekfText.value}，GPS ${gpsStatus.value}。` : (compassFaultActive.value ? '教学罗盘异常尚未排除。' : '需在飞控与传感器页执行一次完整检查。'),
  },
  {
    key: 'rc', title: '遥控系统', section: 'rc',
    state: rcVerificationPassed.value && rcValidationErrors.value.length === 0 ? 'pass' : 'block',
    summary: rcVerificationPassed.value ? '映射 / 行程 / 方向检查通过' : '尚未完成遥控系统验证',
    detail: bridgeMode.value === 'live' && !hasLiveRcInput.value ? 'PX4 SIH 当前无物理 RC 输入；允许使用虚拟教学输入完成通道配置验证。' : `${rcValidationIssues.value.length} 项遥控配置提醒。`,
  },
  {
    key: 'power', title: '动力系统', section: 'power',
    state: engineeringGatePassed.value && !mappingFaultVisible.value && allMotorsVerified.value ? 'pass' : 'block',
    summary: mappingFaultVisible.value ? '存在电机映射故障' : allMotorsVerified.value ? 'M1–M4 单电机测试完成' : `已完成 ${motorNames.filter(m => motorVerified.value[m]).length}/4 个电机测试`,
    detail: '起飞前要求四个电机均完成单独响应确认，并且工程电流裕量通过。',
  },
  {
    key: 'safety', title: '安全设置', section: 'safety',
    state: safetyVerificationPassed.value && safetyValidationErrors.value.length === 0 && safetyScore.value >= 80 ? 'pass' : 'block',
    summary: safetyVerificationPassed.value ? `安全策略得分 ${safetyScore.value}/100` : '尚未执行安全 / Failsafe 验证',
    detail: `${safetyValidationIssues.value.length} 项策略提醒；待应用参数 ${safetyDirtyCount.value} 项。`,
  },
  {
    key: 'prearm', title: 'PX4 Pre-Arm / 最终状态',
    state: prearmPassed.value ? 'pass' : 'block',
    summary: prearmPassed.value ? 'Pre-Arm 未报告阻断' : 'Pre-Arm 当前阻断',
    detail: prearmMessage.value,
  },
])
const preflightBlockers = computed(() => preflightChecks.value.filter(item => item.state === 'block'))
const preflightWarnings = computed(() => preflightChecks.value.filter(item => item.state === 'warn'))
const preflightPassedCount = computed(() => preflightChecks.value.filter(item => item.state === 'pass').length)
const preflightReady = computed(() => preflightBlockers.value.length === 0 && preflightWarnings.value.length === 0)
const preflightScoreValue = computed(() => preflightScore(preflightChecks.value))
const preflightPermitValid = computed(() => Boolean(
  preflightSnapshot.value?.passed
  && preflightSnapshot.value.aircraft_id === (assemblyStore.activeAircraftId ?? null)
  && preflightSnapshot.value.aircraft_fingerprint === aircraftFingerprint(assemblyStore.aircraft)
))
const preflightSavedAtText = computed(() => preflightSnapshot.value?.checked_at
  ? new Date(preflightSnapshot.value.checked_at).toLocaleString('zh-CN', { hour12: false })
  : '—')

const filteredTrainingCases = computed(() => trainingCategoryFilter.value === 'all'
  ? trainingCases.value
  : trainingCases.value.filter(item => item.category === trainingCategoryFilter.value))
const trainingElapsedSeconds = computed(() => {
  clockTick.value
  if (trainingStartedAt.value === null) return 0
  const end = trainingFinishedAt.value ?? Date.now()
  return Math.max(0, Math.floor((end - trainingStartedAt.value) / 1000))
})
const trainingElapsedText = computed(() => formatTrainingDuration(trainingElapsedSeconds.value))
const trainingConditionState = computed<Record<string, boolean>>(() => {
  const rollChannel = Number(rcDraft.value.mapping.roll)
  const rollCalibration = rcDraft.value.channels[rollChannel]
  const standardMapping = Number(rcDraft.value.mapping.roll) === 1
    && Number(rcDraft.value.mapping.pitch) === 2
    && Number(rcDraft.value.mapping.throttle) === 3
    && Number(rcDraft.value.mapping.yaw) === 4
  return {
    compass_repaired: demoCompassRepaired.value,
    sensor_verified: sensorVerificationPassed.value,
    rc_roll_normal: Boolean(rollCalibration && Number(rollCalibration.reverse) === 1),
    rc_mapping_standard: standardMapping,
    rc_verified: rcVerificationPassed.value,
    motor_mapping_repaired: mappingRepaired.value,
    motors_verified: allMotorsVerified.value,
    safety_clean: safetyValidationErrors.value.length === 0,
    safety_verified: safetyVerificationPassed.value,
    preflight_passed: preflightPermitValid.value,
  }
})
const trainingEvaluationPreview = computed(() => activeTrainingCase.value
  ? scoreFaultTraining({
      trainingCase: activeTrainingCase.value,
      conditionState: trainingConditionState.value,
      visitedSections: trainingVisitedSections.value,
      elapsedSeconds: trainingElapsedSeconds.value,
      hintsUsed: trainingHintsUsed.value,
      wrongOperations: trainingWrongOperations.value,
    })
  : null)
const trainingProgressText = computed(() => trainingEvaluationPreview.value
  ? `${trainingEvaluationPreview.value.completedConditions}/${trainingEvaluationPreview.value.totalConditions} 条件完成`
  : '未开始')

const rcChannelOptions = Array.from({ length: 19 }, (_, index) => index)
const liveRcAge = computed(() => liveTelemetry.value?.rc?.age_s ?? null)
const hasLiveRcInput = computed(() => bridgeMode.value === 'live'
  && typeof liveRcAge.value === 'number'
  && liveRcAge.value < 2.5
  && Boolean(liveTelemetry.value?.rc?.channels_us?.some(value => typeof value === 'number')))
const rcInputStale = computed(() => bridgeMode.value === 'live' && !hasLiveRcInput.value)
const currentRcChannels = computed<(number | null)[]>(() => {
  if (!rcVirtualMode.value && hasLiveRcInput.value) {
    const channels = liveTelemetry.value?.rc?.channels_us ?? []
    return Array.from({ length: 18 }, (_, index) => channels[index] ?? null)
  }
  return rcDemoChannels.value.map(value => Number(value))
})
const rcVisibleChannels = computed(() => {
  const count = !rcVirtualMode.value && hasLiveRcInput.value
    ? Math.max(8, Math.min(18, Number(liveTelemetry.value?.rc?.channel_count || 8)))
    : 8
  return Array.from({ length: count }, (_, index) => index + 1)
})
const rcInputSourceText = computed(() => {
  if (rcVirtualMode.value) return bridgeMode.value === 'live' ? '虚拟教学输入（不发送）' : '虚拟遥控教学输入'
  return hasLiveRcInput.value ? 'PX4 RC_CHANNELS' : '无真实 RC 输入'
})
const rcLinkText = computed(() => {
  if (rcVirtualMode.value) return '教学模式'
  if (!hasLiveRcInput.value) return '未检测到'
  const rssi = liveTelemetry.value?.rc?.rssi_percent
  if (typeof rssi === 'number' && rssi < 25) return '信号较弱'
  return '输入正常'
})
const rcLinkClass = computed(() => !rcVirtualMode.value && hasLiveRcInput.value ? 'ok' : rcVirtualMode.value ? 'warn' : 'bad')
const rcRssiText = computed(() => {
  if (rcVirtualMode.value) return '模拟'
  const value = liveTelemetry.value?.rc?.rssi_percent
  return typeof value === 'number' ? `${Math.round(value)}%` : '—'
})
const rcChannelAgeText = computed(() => {
  if (rcVirtualMode.value) return '教学实时'
  const age = liveTelemetry.value?.rc?.age_s
  return typeof age === 'number' ? `${age.toFixed(2)} s` : '待数据'
})
const rcValidationIssues = computed(() => validateRcDraft(rcDraft.value))
const rcValidationErrors = computed(() => rcValidationIssues.value.filter(issue => issue.level === 'error'))
const rcCurrentFlat = computed(() => flattenRcDraft(rcDraft.value))
const rcDirtyKeys = computed(() => Object.entries(rcCurrentFlat.value)
  .filter(([key, value]) => !(key in rcBaselineFlat.value) || Math.abs(Number(value) - Number(rcBaselineFlat.value[key])) > 1e-6)
  .map(([key]) => key))
const rcDirtyCount = computed(() => rcDirtyKeys.value.length)
const rcMappedValues = computed<Record<RcRole, number>>(() => {
  const result = { roll: 0, pitch: 0, throttle: 0, yaw: 0 } as Record<RcRole, number>
  for (const role of rcRoles) {
    const channel = Number(rcDraft.value.mapping[role])
    const calibration = rcDraft.value.channels[channel]
    const pwm = currentRcChannels.value[channel - 1]
    if (!calibration) continue
    result[role] = normalizeRoleInput(role, pwm, calibration)
  }
  return result
})
const leftStickStyle = computed(() => ({
  left: `${50 + rcMappedValues.value.yaw * 38}%`,
  top: `${88 - rcMappedValues.value.throttle * 76}%`,
}))
const rightStickStyle = computed(() => ({
  left: `${50 + rcMappedValues.value.roll * 38}%`,
  top: `${50 - rcMappedValues.value.pitch * 38}%`,
}))
const rcScore = computed(() => calculateRcScore(
  rcDraft.value,
  rcVirtualMode.value || hasLiveRcInput.value,
  rcCaptureComplete.value,
))
const rcLossActionText = computed(() => ({ 0: '禁用', 1: 'Hold', 2: 'Return', 3: 'Land', 5: 'Terminate', 6: 'Disarm', 7: 'Hold' }[Number(safetyDraft.value.NAV_RCL_ACT)] ?? `值 ${safetyDraft.value.NAV_RCL_ACT}`))

const sensorDemoPhase = computed(() => clockTick.value / 10)
const rollDegrees = computed(() => bridgeMode.value === 'live'
  ? (liveTelemetry.value?.attitude.roll ?? 0) * 180 / Math.PI
  : Math.sin(sensorDemoPhase.value * .65) * 2.2)
const pitchDegrees = computed(() => bridgeMode.value === 'live'
  ? (liveTelemetry.value?.attitude.pitch ?? 0) * 180 / Math.PI
  : Math.cos(sensorDemoPhase.value * .52) * 1.4)
const yawDegrees = computed(() => {
  const live = liveTelemetry.value?.magnetometer?.heading_deg
  if (bridgeMode.value === 'live' && typeof live === 'number') return live
  if (bridgeMode.value === 'live') return ((liveTelemetry.value?.attitude.yaw ?? 0) * 180 / Math.PI + 360) % 360
  return compassFaultActive.value ? 287 + Math.sin(sensorDemoPhase.value) * 18 : 42 + Math.sin(sensorDemoPhase.value * .22) * 2
})
const headingDegrees = computed(() => ((yawDegrees.value % 360) + 360) % 360)
const rollDegText = computed(() => `${rollDegrees.value.toFixed(1)}°`)
const pitchDegText = computed(() => `${pitchDegrees.value.toFixed(1)}°`)
const yawDegText = computed(() => `${headingDegrees.value.toFixed(1)}°`)
const headingText = computed(() => `${Math.round(headingDegrees.value).toString().padStart(3, '0')}°`)
const attitudeTransform = computed(() => {
  const offset = Math.max(-42, Math.min(42, pitchDegrees.value * 2.0))
  return `translateY(${offset}px) rotate(${-rollDegrees.value}deg)`
})
const heartbeatText = computed(() => {
  if (bridgeMode.value !== 'live') return '模拟'
  const age = liveTelemetry.value?.heartbeat_age_s
  return typeof age === 'number' ? `${age.toFixed(1)} s` : '—'
})

const imuAccel = computed(() => {
  const live = liveTelemetry.value?.imu?.accel_m_s2
  if (bridgeMode.value === 'live' && live) return live
  const t = sensorDemoPhase.value
  return { x: Math.sin(t * .8) * .08, y: Math.cos(t * .7) * .06, z: 9.806 + Math.sin(t * .25) * .03 }
})
const imuGyro = computed(() => {
  const live = liveTelemetry.value?.imu?.gyro_rad_s
  if (bridgeMode.value === 'live' && live) return live
  const t = sensorDemoPhase.value
  return { x: Math.sin(t * .55) * .006, y: Math.cos(t * .42) * .005, z: Math.sin(t * .31) * .004 }
})
const imuSourceText = computed(() => bridgeMode.value === 'live'
  ? (liveTelemetry.value?.imu?.source || '等待 IMU 数据')
  : '教学模拟')
const temperatureText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.imu?.temperature_c : 31.8
  return typeof value === 'number' ? `${value.toFixed(1)} °C` : '—'
})
const imuAgeText = computed(() => formatAge(liveTelemetry.value?.sensor_data_age_s?.imu))
const barometerAgeText = computed(() => formatAge(liveTelemetry.value?.sensor_data_age_s?.barometer))

const gpsFixText = computed(() => bridgeMode.value === 'live' ? `Fix ${liveTelemetry.value?.gps.fix_type ?? '—'}` : 'Fix 3D')
const gpsSatelliteText = computed(() => bridgeMode.value === 'live' ? `${liveTelemetry.value?.gps.satellites ?? '—'}` : '12')
const gpsEphText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.gps.eph : .72
  return typeof value === 'number' ? `${value.toFixed(2)} m` : '—'
})
const latitudeText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.global_position.lat_deg : 31.230416
  return typeof value === 'number' ? value.toFixed(6) : '—'
})
const longitudeText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.global_position.lon_deg : 121.473701
  return typeof value === 'number' ? value.toFixed(6) : '—'
})
const globalAltitudeText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.global_position.relative_alt_m : 0
  return typeof value === 'number' ? `${value.toFixed(2)} m` : '—'
})

const magneticFieldText = computed(() => {
  const value = bridgeMode.value === 'live'
    ? liveTelemetry.value?.magnetometer?.field_strength_gauss
    : (compassFaultActive.value ? 1.42 : .48)
  return typeof value === 'number' ? `${value.toFixed(3)} G` : '—'
})
const magneticVectorText = computed(() => {
  const mag = bridgeMode.value === 'live' ? liveTelemetry.value?.magnetometer : null
  if (mag && [mag.x_gauss, mag.y_gauss, mag.z_gauss].every(value => typeof value === 'number')) {
    return `${mag.x_gauss!.toFixed(2)} / ${mag.y_gauss!.toFixed(2)} / ${mag.z_gauss!.toFixed(2)} G`
  }
  return compassFaultActive.value ? '1.26 / 0.54 / 0.39 G' : '0.23 / 0.10 / 0.41 G'
})
const pressureAltitudeText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.barometer?.pressure_alt_m : 18.4
  return typeof value === 'number' ? `${value.toFixed(1)} m` : '—'
})
const pressureText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.barometer?.absolute_pressure_hpa : 1011.8
  return typeof value === 'number' ? `${value.toFixed(1)} hPa` : '—'
})
const baroTemperatureText = computed(() => {
  const value = bridgeMode.value === 'live' ? liveTelemetry.value?.barometer?.temperature_c : 27.6
  return typeof value === 'number' ? `${value.toFixed(1)} °C` : '—'
})
const estimatorFlagsText = computed(() => {
  if (bridgeMode.value !== 'live') return compassFaultActive.value ? '0x00000008' : '0x000003FF'
  const flags = liveTelemetry.value?.estimator.flags
  return typeof flags === 'number' ? `0x${flags.toString(16).toUpperCase().padStart(8, '0')}` : '—'
})
const localPositionText = computed(() => {
  const p = bridgeMode.value === 'live' ? liveTelemetry.value?.local_position : { x: 0, y: 0, z: 0 }
  return p ? `${p.x.toFixed(2)} / ${p.y.toFixed(2)} / ${p.z.toFixed(2)} m` : '—'
})
const ekfDiagnosisText = computed(() => {
  if (bridgeMode.value === 'live') {
    if (liveTelemetry.value?.estimator.ok === true) return '状态估计器正在输出有效状态；结合 Pre-Arm 与 STATUSTEXT 继续判断。'
    if (liveTelemetry.value?.estimator.ok === false) return 'Estimator flags 未达到当前健康判断，请检查传感器数据与 PX4 状态文本。'
    return '等待 ESTIMATOR_STATUS 数据。'
  }
  return compassFaultActive.value ? '航向数据偏离，EKF 教学状态被标记为异常。' : '姿态、位置与航向估计处于教学正常状态。'
})

function formatSensorValue(value: number | null | undefined, digits = 2): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : '—'
}

function formatAge(value: number | null | undefined): string {
  if (bridgeMode.value !== 'live') return '模拟'
  return typeof value === 'number' ? `${value.toFixed(2)} s` : '待数据'
}

function sensorState(name: SensorHealthName): 'ok' | 'warn' | 'unknown' {
  if (bridgeMode.value !== 'live') {
    if (name === 'magnetometer' && compassFaultActive.value) return 'warn'
    return 'ok'
  }
  if (name === 'gps') return gpsHealthy.value ? 'ok' : 'warn'
  const flag = liveTelemetry.value?.sensor_health?.[name]
  if (flag?.healthy === true) return 'ok'
  if (flag?.healthy === false) return 'warn'
  const ageKey = name === 'gyro' || name === 'accelerometer' ? 'imu' : name
  const age = liveTelemetry.value?.sensor_data_age_s?.[ageKey as 'imu' | 'magnetometer' | 'barometer']
  if (typeof age === 'number' && age < 2.5) return 'ok'
  return 'unknown'
}

function sensorStatusClass(name: SensorHealthName): string { return sensorState(name) }
function sensorStatusText(name: SensorHealthName): string {
  const state = sensorState(name)
  return state === 'ok' ? '正常' : state === 'warn' ? '异常' : '待数据'
}
const imuHealthClass = computed(() => sensorState('gyro') === 'warn' || sensorState('accelerometer') === 'warn'
  ? 'warn'
  : sensorState('gyro') === 'ok' && sensorState('accelerometer') === 'ok' ? 'ok' : 'unknown')
const imuHealthText = computed(() => imuHealthClass.value === 'ok' ? 'IMU 正常' : imuHealthClass.value === 'warn' ? 'IMU 异常' : '等待数据')

const motorRows = computed(() => motorNames.map(motor => {
  const isCommanded = commandedMotor.value === motor
  const actual = actualMotor.value
  const response = isCommanded
    ? actual === motor ? '响应正确' : actual ? `实际 ${actual} 响应` : '待测试'
    : '—'
  return {
    motor,
    position: motorMeta[motor].position,
    direction: motorMeta[motor].direction,
    response,
    responseClass: isCommanded && actual && actual !== motor ? 'response-fault' : isCommanded && actual === motor ? 'response-ok' : '',
  }
}))

function liveFlightMode(): TelemetryFrame['flight_mode'] {
  if (!liveTelemetry.value?.armed) return 'IDLE'
  const altitude = liveTelemetry.value.local_position.z
  const vz = liveTelemetry.value.local_position.vz
  if (altitude < .25) return 'ARMED'
  if (vz > .25) return 'TAKING_OFF'
  if (vz < -.25) return 'LANDING'
  return 'HOVERING'
}

const debugTelemetry = computed<TelemetryFrame>(() => {
  const live = bridgeMode.value === 'live' ? liveTelemetry.value : null
  const outputs = motorOutputs.value
  if (live) {
    const remaining = typeof live.battery.remaining === 'number' ? live.battery.remaining / 100 : .86
    return {
      t: clockTick.value / 10,
      position: { ...live.local_position },
      velocity: { x: live.local_position.vx, y: live.local_position.vy, z: live.local_position.vz },
      attitude: { roll: live.attitude.roll, pitch: live.attitude.pitch, yaw: live.attitude.yaw },
      angular_velocity: { p: live.attitude.rollspeed, q: live.attitude.pitchspeed, r: live.attitude.yawspeed },
      center_of_gravity: engineering.value?.center_of_gravity_m ?? { x: 0, y: 0, z: 0 },
      motors: {
        outputs: [...outputs] as MotorVector,
        thrusts_n: outputs.map(item => item * maxThrustPerMotor.value) as MotorVector,
      },
      forces: { gravity_n: gravityN.value, total_thrust_n: totalThrustN.value },
      wind: { speed_mps: 0, direction_deg: 0 },
      power: {
        estimated_power_w: engineering.value?.hover_power_w ?? 0,
        battery_remaining: Math.max(0, Math.min(1, remaining)),
        voltage_v: live.battery.voltage_v ?? configuredBatteryVoltage.value,
        current_a: live.battery.current_a ?? 0,
      },
      armed: live.armed,
      flight_mode: liveFlightMode(),
    }
  }
  return {
    t: clockTick.value / 10,
    position: { x: 0, y: 0, z: 0 },
    velocity: { x: 0, y: 0, z: 0 },
    attitude: { roll: 0, pitch: 0, yaw: 0 },
    angular_velocity: { p: 0, q: 0, r: 0 },
    center_of_gravity: engineering.value?.center_of_gravity_m ?? { x: 0, y: 0, z: 0 },
    motors: {
      outputs: [...outputs] as MotorVector,
      thrusts_n: outputs.map(item => item * maxThrustPerMotor.value) as MotorVector,
    },
    forces: { gravity_n: gravityN.value, total_thrust_n: totalThrustN.value },
    wind: { speed_mps: 0, direction_deg: 0 },
    power: {
      estimated_power_w: engineering.value?.hover_power_w ?? 0,
      battery_remaining: .86,
      voltage_v: configuredBatteryVoltage.value + .2,
      current_a: outputs.reduce((sum, item) => sum + item * 7.5, 0),
    },
    armed: false,
    flight_mode: 'IDLE',
  }
})

function nowText(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function appendLog(title: string, detail = '教学调试操作', level: LogLevel = 'info'): void {
  logs.value.push({ id: ++logId, time: nowText(), title, detail, level })
  if (logs.value.length > 12) logs.value = logs.value.slice(-12)
  if (
    activeTrainingCase.value
    && !trainingInternalMutation
    && level === 'error'
    && /(失败|拒绝|超时)/.test(title)
  ) {
    trainingWrongOperations.value += 1
  }
}

function trainingHasInjection(key: string): boolean {
  return Boolean(activeTrainingCase.value?.injections.includes(key))
}

function trainingDifficulty(value: number): string {
  return trainingDifficultyText(value)
}

function trainingCategoryLabel(category: TrainingCategory): string {
  return trainingCategoryText(category)
}

function formatTrainingDuration(seconds: number): string {
  const value = Math.max(0, Math.floor(seconds))
  const minutes = Math.floor(value / 60)
  const remainder = value % 60
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

function applyTrainingRcInjections(trainingCase: FaultTrainingCase): void {
  if (!trainingCase.injections.some(key => key === 'rc_roll_reverse' || key === 'rc_mapping_swap')) return
  const next = defaultRcDraft(18)
  if (trainingCase.injections.includes('rc_roll_reverse')) {
    next.channels[1].reverse = -1
  }
  if (trainingCase.injections.includes('rc_mapping_swap')) {
    next.mapping.roll = 2
    next.mapping.pitch = 1
  }
  rcDraft.value = cloneRcDraft(next)
  rcBaselineFlat.value = flattenRcDraft(next)
  rcLoadedOnce.value = true
  rcVirtualMode.value = true
  rcCaptureComplete.value = false
  rcVerificationPassed.value = false
  rcMessageLevel.value = 'warn'
  rcMessage.value = '案例已载入遥控教学异常。请根据实时输入与映射表自行定位。'
}

function applyTrainingSafetyInjection(trainingCase: FaultTrainingCase): void {
  if (!trainingCase.injections.includes('failsafe_profile')) return
  safetyDraft.value = { ...unsafeDemoSafetyProfile }
  safetyBaseline.value = { ...unsafeDemoSafetyProfile }
  safetyDirty.value = {}
  safetyLoadedOnce.value = true
  safetyVerificationPassed.value = false
  demoFailsafeRepaired.value = false
  safetyMessageLevel.value = 'warn'
  safetyMessage.value = '案例已载入安全策略异常。请使用策略检查定位风险。'
}

function applyTrainingCaseInjections(trainingCase: FaultTrainingCase): void {
  applyTrainingRcInjections(trainingCase)
  applyTrainingSafetyInjection(trainingCase)
  if (trainingCase.injections.includes('compass_fault')) {
    demoCompassRepaired.value = false
    sensorVerificationPassed.value = false
  }
  if (trainingCase.injections.includes('motor_mapping')) {
    mappingRepaired.value = false
    motorVerified.value = { M1: false, M2: false, M3: false, M4: false }
  }
  invalidatePreflightPermit()
}

function startTrainingCase(trainingCase: FaultTrainingCase): void {
  if (assignedScenarioId.value && assignedScenarioId.value !== trainingCase.id) {
    trainingCatalogError.value = `当前教师任务指定案例 ${assignedScenarioId.value}，不能切换到 ${trainingCase.id}。`
    return
  }
  trainingInternalMutation = true
  activeTrainingCase.value = trainingCase
  trainingLibraryOpen.value = false
  trainingStartedAt.value = Date.now()
  trainingFinishedAt.value = null
  trainingVisitedSections.value = []
  trainingHintsUsed.value = 0
  trainingWrongOperations.value = 0
  trainingCurrentHint.value = ''
  trainingSubmittedEvaluation.value = null
  trainingRemoteStatus.value = assignedRunId.value ? '正在记录课程实训过程' : ''

  // Avoid a watcher loading normal parameters between scenario reset and injection.
  activeSection.value = 'power'
  switchScenario(trainingCase.legacy_scenario)
  applyTrainingCaseInjections(trainingCase)
  activeSection.value = trainingCase.initial_section
  trainingVisitedSections.value = [trainingCase.initial_section]
  trainingInternalMutation = false

  appendLog(
    `开始实训案例 ${trainingCase.id}`,
    `${trainingCase.title} · ${trainingCase.fault_source} · 建议 ${trainingCase.recommended_minutes} 分钟`,
    'warn',
  )
}

function restartTrainingCase(): void {
  if (activeTrainingCase.value) startTrainingCase(activeTrainingCase.value)
}

function enterFreeDebug(): void {
  if (assignedRunId.value) {
    appendLog('课程实训已锁定案例', '请完成教师发布的案例后再返回自由调试。', 'warn')
    return
  }
  trainingInternalMutation = true
  activeTrainingCase.value = null
  trainingStartedAt.value = null
  trainingFinishedAt.value = null
  trainingVisitedSections.value = []
  trainingHintsUsed.value = 0
  trainingWrongOperations.value = 0
  trainingCurrentHint.value = ''
  trainingSubmittedEvaluation.value = null
  switchScenario('standard')

  const rc = defaultRcDraft(18)
  rcDraft.value = cloneRcDraft(rc)
  rcBaselineFlat.value = flattenRcDraft(rc)
  rcLoadedOnce.value = true
  rcVerificationPassed.value = false
  safetyDraft.value = { ...recommendedSafetyProfile }
  safetyBaseline.value = { ...recommendedSafetyProfile }
  safetyDirty.value = {}
  safetyLoadedOnce.value = true
  safetyVerificationPassed.value = false
  trainingInternalMutation = false
  appendLog('进入自由调试', '已退出故障案例，恢复教学默认配置。', 'info')
}

function requestTrainingHint(): void {
  const trainingCase = activeTrainingCase.value
  if (!trainingCase) return
  if (trainingHintsUsed.value >= trainingCase.hints.length) {
    trainingCurrentHint.value = '本案例没有更多提示。'
    return
  }
  trainingCurrentHint.value = trainingCase.hints[trainingHintsUsed.value]
  trainingHintsUsed.value += 1
  appendLog('使用案例提示', `已使用第 ${trainingHintsUsed.value} 条提示；本次评分将扣除提示分。`, 'warn')
}

async function submitTrainingCase(): Promise<void> {
  if (!activeTrainingCase.value) return
  const worksheet = diagnosisWorksheetRef.value
  if (auth.user?.role === 'student' && assignedRunId.value && !worksheet?.isComplete()) {
    trainingCurrentHint.value = '提交课程诊断前，请先完成诊断工作单的现象、证据、原因、修复和验证五项。'
    appendLog('诊断工作单未完成', '课程任务要求先形成完整证据链，再提交诊断。', 'warn')
    return
  }
  if (worksheet) await worksheet.save()
  const evaluation = trainingEvaluationPreview.value
  if (!evaluation) return
  trainingSubmittedEvaluation.value = { ...evaluation }
  if (evaluation.passed) {
    trainingFinishedAt.value = Date.now()
    appendLog('实训案例完成', `${activeTrainingCase.value.id} · 案例得分 ${evaluation.score}/100`, 'success')
  } else {
    appendLog('案例提交未通过', `当前完成 ${evaluation.completedConditions}/${evaluation.totalConditions} 个成功条件，可继续诊断后再次提交。`, 'warn')
  }

  if (!assignedRunId.value) return
  try {
    const run = await studentTrainingApi.submitRun(assignedRunId.value, trainingPayload(evaluation.passed))
    trainingRemoteStatus.value = run.stage === 'awaiting_flight'
      ? `诊断已提交 · 当前课程成绩 ${run.score ?? '—'} · 等待飞行验证`
      : run.status === 'completed'
        ? `课程实训已完成 · 最终成绩 ${run.score ?? '—'}`
        : `诊断已同步 · 当前阶段 ${run.stage}`
    if (run.stage === 'awaiting_flight') {
      appendLog('进入下一阶段', 'Pre-Arm 已通过，请进入 PX4 飞行验证完成课程任务。', 'success')
    }
  } catch (error) {
    trainingRemoteStatus.value = `课程实训同步失败：${errorText(error)}`
  }
}

function trainingPayload(passed = false) {
  const evaluation = trainingEvaluationPreview.value
  return {
    passed,
    score: evaluation?.score ?? 0,
    elapsed_seconds: trainingElapsedSeconds.value,
    hints_used: trainingHintsUsed.value,
    wrong_operations: trainingWrongOperations.value,
    prearm_passed: preflightPermitValid.value,
    flight_validation_passed: false,
    result: {
      case_id: activeTrainingCase.value?.id ?? assignedScenarioId.value,
      case_title: activeTrainingCase.value?.title ?? '',
      bridge_mode: bridgeMode.value,
      visited_sections: [...trainingVisitedSections.value],
      condition_state: { ...trainingConditionState.value },
      evaluation,
      diagnosis_worksheet: diagnosisWorksheetRef.value?.getSnapshot() ?? null,
    },
  }
}

function scheduleTrainingProgressSync(delay = 450): void {
  if (!assignedRunId.value || !activeTrainingCase.value || trainingInternalMutation) return
  if (trainingSyncTimer) window.clearTimeout(trainingSyncTimer)
  trainingSyncTimer = window.setTimeout(() => { void syncTrainingProgress() }, delay)
}

async function syncTrainingProgress(): Promise<void> {
  if (!assignedRunId.value || !activeTrainingCase.value || trainingSyncBusy) return
  trainingSyncBusy = true
  try {
    const run = await studentTrainingApi.progressRun(assignedRunId.value, trainingPayload(false))
    trainingRemoteStatus.value = `课程实训记录中 · ${run.stage}`
  } catch (error) {
    trainingRemoteStatus.value = `过程记录暂未同步：${errorText(error)}`
  } finally {
    trainingSyncBusy = false
  }
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function switchScenario(next: ScenarioKey): void {
  scenario.value = next
  mappingRepaired.value = false
  demoCompassRepaired.value = false
  demoFailsafeRepaired.value = false
  sensorVerificationPassed.value = false
  rcVerificationPassed.value = false
  safetyVerificationPassed.value = false
  motorVerified.value = { M1: false, M2: false, M3: false, M4: false }
  invalidatePreflightPermit()
  safetyLoadedOnce.value = false
  calibrationState.value = { gyro: 'idle', accelerometer: 'idle', compass: 'idle', barometer: 'idle' }
  calibrationMessage.value = { gyro: '', accelerometer: '', compass: '', barometer: '' }
  stopAllMotors()
  if (!trainingInternalMutation) {
    appendLog(`切换训练场景：${scenarios.find(item => item.key === next)?.title ?? next}`, bridgeMode.value === 'live' ? '真实 PX4 模式不注入前端故障；场景仅保留教学说明' : '场景状态已重新初始化', 'info')
  }
  if (activeSection.value === 'safety') void loadSafetyParameters()
}

async function pollPx4(): Promise<void> {
  if (pollingPx4) return
  pollingPx4 = true
  try {
    const telemetry = await px4Api.telemetry()
    liveTelemetry.value = telemetry
    if (!telemetry.dependency_available) {
      bridgeMode.value = 'demo'
      bridgeError.value = 'Bridge 缺少 pymavlink，请安装 requirements.txt'
    } else if (telemetry.connected) {
      const justConnected = bridgeMode.value !== 'live'
      bridgeMode.value = 'live'
      bridgeError.value = ''
      if (justConnected) appendLog('PX4 SIH 已连接', `收到 Heartbeat · System ${telemetry.system_id ?? '—'}`, 'success')
      if (!requestedStreams.value) {
        requestedStreams.value = true
        void px4Api.requestStreams().catch(() => { requestedStreams.value = false })
      }
      if (!motorTestBusy.value && telemetry.motors.outputs.length >= 4) {
        motorOutputs.value = telemetry.motors.outputs.slice(0, 4).map(value => Math.max(0, Math.min(1, value))) as MotorVector
      }
    } else {
      bridgeMode.value = 'demo'
      bridgeError.value = telemetry.running ? 'Bridge 已启动，等待 PX4 Heartbeat (UDP 14540)' : (telemetry.last_error || 'PX4 Bridge 未运行')
    }
  } catch (error) {
    bridgeMode.value = 'demo'
    bridgeError.value = `无法访问 PX4 Bridge：${errorText(error)}`
  } finally {
    pollingPx4 = false
  }
}

async function connectPx4(): Promise<void> {
  bridgeBusy.value = true
  try {
    const status = await px4Api.connect()
    bridgeError.value = status.connected ? '' : 'Bridge 已监听 14540，等待 PX4 SIH Heartbeat'
    appendLog('启动 PX4 Bridge 连接', status.connection_url, status.connected ? 'success' : 'warn')
    await new Promise(resolve => window.setTimeout(resolve, 450))
    await pollPx4()
  } catch (error) {
    bridgeError.value = errorText(error)
    appendLog('PX4 连接失败', bridgeError.value, 'error')
  } finally {
    bridgeBusy.value = false
  }
}

async function withBridgeAction(title: string, action: () => Promise<unknown>): Promise<void> {
  bridgeBusy.value = true
  try {
    await action()
    appendLog(title, 'PX4 已接受 MAVLink 指令', 'success')
    await pollPx4()
  } catch (error) {
    appendLog(`${title}失败`, errorText(error), 'error')
  } finally {
    bridgeBusy.value = false
  }
}

function armPx4(): Promise<void> { return withBridgeAction('PX4 解锁', () => px4Api.arm()) }
function disarmPx4(): Promise<void> { return withBridgeAction('PX4 上锁', () => px4Api.disarm()) }
function takeoffPx4(): Promise<void> { return withBridgeAction('PX4 起飞 2m', () => px4Api.takeoff(2)) }
function landPx4(): Promise<void> { return withBridgeAction('PX4 降落', () => px4Api.land()) }
function runPrearmPx4(): Promise<void> { return withBridgeAction('执行 PX4 Pre-Arm Check', () => px4Api.prearmCheck()) }

async function readPx4Parameter(): Promise<void> {
  bridgeBusy.value = true
  paramMessage.value = ''
  try {
    const result = await px4Api.getParameter(paramName.value)
    paramValue.value = result.value
    paramMessage.value = `${result.name} = ${result.value}`
    appendLog('读取 PX4 参数', paramMessage.value, 'info')
  } catch (error) {
    paramMessage.value = errorText(error)
    appendLog('参数读取失败', paramMessage.value, 'error')
  } finally {
    bridgeBusy.value = false
  }
}

async function writePx4Parameter(): Promise<void> {
  if (paramValue.value === null) return
  bridgeBusy.value = true
  paramMessage.value = ''
  try {
    const result = await px4Api.setParameter(paramName.value, Number(paramValue.value))
    paramValue.value = result.value
    paramMessage.value = `${result.name} 已写入 ${result.value}`
    appendLog('修改 PX4 参数', paramMessage.value, 'success')
  } catch (error) {
    paramMessage.value = errorText(error)
    appendLog('参数写入失败', paramMessage.value, 'error')
  } finally {
    bridgeBusy.value = false
  }
}

function calibrationStateText(key: Px4SensorKey): string {
  const state = calibrationState.value[key]
  if (state === 'running') return '执行中'
  if (state === 'requested') return calibrationMessage.value[key] || 'PX4 已受理'
  if (state === 'passed') return calibrationMessage.value[key] || '教学流程完成'
  if (state === 'failed') return calibrationMessage.value[key] || '执行失败'
  return '尚未执行'
}

function calibrationButtonText(key: Px4SensorKey): string {
  const state = calibrationState.value[key]
  if (state === 'running') return '执行中…'
  if (state === 'requested') return '重新发起'
  return state === 'passed' ? '重新校准' : '开始校准'
}

async function calibrateSensor(key: Px4SensorKey): Promise<void> {
  sensorVerificationPassed.value = false
  invalidatePreflightPermit()
  if (sensorActionBusy.value) return
  sensorActionBusy.value = true
  calibrationState.value[key] = 'running'
  calibrationMessage.value[key] = ''
  const title = sensorCalibrations.find(item => item.key === key)?.title ?? key
  const teachingCompassInjection = key === 'compass' && trainingHasInjection('compass_fault')
  appendLog(`开始${title}`, bridgeMode.value === 'live' && !teachingCompassInjection ? '向 PX4 发送飞行前校准命令' : '进入教学故障校准流程', 'info')
  try {
    if (bridgeMode.value === 'live' && !teachingCompassInjection) {
      if (px4Armed.value) throw new Error('请先上锁，PX4 仅在飞行前状态接受传感器校准')
      const result = await px4Api.calibrateSensor(key)
      if (!result.accepted) throw new Error(result.timeout ? '等待 PX4 校准 ACK 超时' : `PX4 拒绝校准命令（result ${result.result ?? 'unknown'}）`)
      calibrationState.value[key] = 'requested'
      calibrationMessage.value[key] = '命令已受理，请按 PX4 STATUSTEXT 提示完成动作'
      appendLog(`${title}指令已受理`, '继续观察 PX4 STATUSTEXT；命令受理不等于校准已经完成。', 'success')
      await pollPx4()
    } else {
      await new Promise(resolve => window.setTimeout(resolve, key === 'accelerometer' || key === 'compass' ? 900 : 550))
      calibrationState.value[key] = 'passed'
      calibrationMessage.value[key] = '教学模拟流程完成'
      if (key === 'compass' && (scenario.value === 'compass' || trainingHasInjection('compass_fault'))) {
        demoCompassRepaired.value = true
        appendLog('罗盘教学故障已排除', '磁场强度与航向恢复到教学正常范围，EKF 状态恢复。', 'success')
      } else {
        appendLog(`${title}完成`, '教学模拟：已完成操作流程与结果复核。', 'success')
      }
    }
  } catch (error) {
    calibrationState.value[key] = 'failed'
    calibrationMessage.value[key] = errorText(error)
    appendLog(`${title}失败`, calibrationMessage.value[key], 'error')
  } finally {
    sensorActionBusy.value = false
  }
}

async function runSensorDiagnostic(): Promise<void> {
  if (sensorActionBusy.value) return
  sensorActionBusy.value = true
  appendLog('执行传感器检查', bridgeMode.value === 'live' ? '刷新 MAVLink 数据流并运行 PX4 Pre-Arm Check' : '检查教学模拟传感器健康与 EKF 状态', 'info')
  try {
    if (bridgeMode.value === 'live' && !trainingHasInjection('compass_fault')) {
      await px4Api.requestStreams()
      await px4Api.prearmCheck()
      await new Promise(resolve => window.setTimeout(resolve, 250))
      await pollPx4()
      sensorVerificationPassed.value = ekfOk.value && gpsHealthy.value
      appendLog('传感器检查完成', prearmPassed.value ? 'PX4 当前未报告 Pre-Arm 阻断。' : (liveTelemetry.value?.statustext || '存在 Pre-Arm 阻断，请查看状态。'), sensorVerificationPassed.value ? 'success' : 'warn')
    } else {
      await new Promise(resolve => window.setTimeout(resolve, 450))
      sensorVerificationPassed.value = !compassFaultActive.value && ekfOk.value && gpsHealthy.value
      appendLog('教学传感器检查完成', compassFaultActive.value ? '发现罗盘/EKF 教学异常，建议执行罗盘校准。' : 'IMU、GPS、罗盘、气压计与 EKF 教学状态正常。', sensorVerificationPassed.value ? 'success' : 'warn')
    }
  } catch (error) {
    sensorVerificationPassed.value = false
    appendLog('传感器检查失败', errorText(error), 'error')
  } finally {
    sensorActionBusy.value = false
  }
}



function normalizeRoleInput(role: RcRole, pwm: number | null | undefined, calibration: import('../utils/rc').RcChannelCalibration): number {
  return normalizeRcInput(pwm, calibration, role === 'throttle')
}

function ensureRcCalibration(channel: number): void {
  const key = Number(channel)
  if (!Number.isInteger(key) || key < 0 || key > 18) return
  if (rcDraft.value.channels[key]) return
  rcDraft.value.channels[key] = {
    min: 1000,
    trim: key === Number(rcDraft.value.mapping.throttle) ? 1000 : 1500,
    max: 2000,
    reverse: 1,
    deadzone: 10,
  }
}

function setDemoRcChannel(index: number, event: Event): void {
  const value = Number((event.target as HTMLInputElement).value)
  rcDemoChannels.value[index] = Math.max(800, Math.min(2200, value))
  rcDemoChannels.value = [...rcDemoChannels.value]
}

function resetVirtualRc(): void {
  rcDemoChannels.value = [1500, 1500, 1000, 1500, ...Array(14).fill(1500)]
  appendLog('虚拟遥控回中', 'Roll/Pitch/Yaw 回到 1500 μs，Throttle 回到 1000 μs。', 'info')
}

function rcChannelValue(channel: number): string {
  const value = currentRcChannels.value[channel - 1]
  return typeof value === 'number' ? `${Math.round(value)} μs` : '—'
}

function rcChannelBarPercent(channel: number): string {
  const value = currentRcChannels.value[channel - 1]
  if (typeof value !== 'number') return '0%'
  return `${Math.max(0, Math.min(100, (value - 800) / 14))}%`
}

function rcChannelRoles(channel: number): string {
  const roles = rcRoles.filter(role => Number(rcDraft.value.mapping[role]) === channel)
  return roles.length ? roles.map(role => rcRoleLabels[role].split(' ')[0]).join(' / ') : '未映射'
}

function formatRcSigned(value: number): string {
  const safe = Math.max(-1, Math.min(1, Number(value) || 0))
  return `${safe >= 0 ? '+' : ''}${(safe * 100).toFixed(0)}%`
}

function formatRcPercent(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, Number(value) || 0)) * 100)}%`
}

function rcRoleMeterWidth(role: RcRole): string {
  const value = rcMappedValues.value[role]
  return role === 'throttle'
    ? `${Math.max(0, Math.min(1, value)) * 100}%`
    : `${Math.max(0, Math.min(1, (value + 1) / 2)) * 100}%`
}

function updateRcCapture(values = currentRcChannels.value): void {
  if (!rcCaptureActive.value) return
  const nextMin = [...rcObservedMin.value]
  const nextMax = [...rcObservedMax.value]
  values.forEach((value, index) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) return
    nextMin[index] = Math.min(nextMin[index], value)
    nextMax[index] = Math.max(nextMax[index], value)
  })
  rcObservedMin.value = nextMin
  rcObservedMax.value = nextMax
}

function startRcCapture(): void {
  rcObservedMin.value = Array(18).fill(Number.POSITIVE_INFINITY)
  rcObservedMax.value = Array(18).fill(Number.NEGATIVE_INFINITY)
  rcCaptureActive.value = true
  rcCaptureComplete.value = false
  updateRcCapture()
  appendLog('开始遥控行程采集', '请缓慢移动四个主控制摇杆到所有端点，再返回中位。', 'info')
}

function finishRcCapture(): void {
  if (!rcCaptureActive.value) return
  updateRcCapture()
  let updated = 0
  const mapped = new Set(rcRoles.map(role => Number(rcDraft.value.mapping[role])).filter(channel => channel >= 1 && channel <= 18))
  for (const channel of mapped) {
    ensureRcCalibration(channel)
    const min = rcObservedMin.value[channel - 1]
    const max = rcObservedMax.value[channel - 1]
    if (!Number.isFinite(min) || !Number.isFinite(max) || max - min < 200) continue
    rcDraft.value.channels[channel].min = Math.round(min)
    rcDraft.value.channels[channel].max = Math.round(max)
    if (channel === Number(rcDraft.value.mapping.throttle)) {
      rcDraft.value.channels[channel].trim = Math.round(min)
    }
    updated += 1
  }
  rcCaptureActive.value = false
  rcCaptureComplete.value = updated > 0
  rcMessageLevel.value = updated > 0 ? 'success' : 'warn'
  rcMessage.value = updated > 0
    ? `已从本次输入采集 ${updated} 个主通道的 Min/Max，仅写入本地草稿。`
    : '没有采集到足够的摇杆行程，请重新开始并将摇杆移动到端点。'
  appendLog('结束遥控行程采集', rcMessage.value, updated > 0 ? 'success' : 'warn')
}

function captureRcCenters(): void {
  let updated = 0
  for (const role of ['roll', 'pitch', 'yaw'] as RcRole[]) {
    const channel = Number(rcDraft.value.mapping[role])
    if (channel < 1 || channel > 18) continue
    ensureRcCalibration(channel)
    const value = currentRcChannels.value[channel - 1]
    if (typeof value !== 'number') continue
    rcDraft.value.channels[channel].trim = Math.round(value)
    updated += 1
  }
  const throttleChannel = Number(rcDraft.value.mapping.throttle)
  if (throttleChannel >= 1 && throttleChannel <= 18) {
    ensureRcCalibration(throttleChannel)
    rcDraft.value.channels[throttleChannel].trim = rcDraft.value.channels[throttleChannel].min
  }
  rcMessageLevel.value = updated > 0 ? 'success' : 'warn'
  rcMessage.value = updated > 0 ? '已采集 Roll/Pitch/Yaw 当前中位；Throttle Trim 使用 Min。' : '当前没有可用输入值。'
  appendLog('采集遥控中位', rcMessage.value, updated > 0 ? 'success' : 'warn')
}

function rcObservedRangeText(role: RcRole): string {
  const channel = Number(rcDraft.value.mapping[role])
  const min = rcObservedMin.value[channel - 1]
  const max = rcObservedMax.value[channel - 1]
  if (!Number.isFinite(min) || !Number.isFinite(max)) return '—'
  return `${Math.round(min)} – ${Math.round(max)} μs`
}

function loadRecommendedRcProfile(): void {
  const next = defaultRcDraft(18)
  rcDraft.value = cloneRcDraft(next)
  rcMessageLevel.value = 'info'
  rcMessage.value = `已载入教学推荐遥控配置，${rcDirtyCount.value} 项等待应用。`
  appendLog('载入教学推荐遥控配置', 'CH1 Roll / CH2 Pitch / CH3 Throttle / CH4 Yaw，标准 1000–2000 μs 行程。', 'info')
}

async function loadRcParameters(): Promise<void> {
  if (rcBusy.value) return
  rcBusy.value = true
  rcMessage.value = ''
  try {
    if (bridgeMode.value === 'live') {
      const next = defaultRcDraft(18)
      const failed: string[] = []
      for (const role of rcRoles) {
        try {
          const result = await px4Api.getParameter(rcMapParams[role])
          const channel = Math.max(0, Math.min(18, Math.round(Number(result.value))))
          next.mapping[role] = channel
          ensureRcCalibrationForDraft(next, channel)
        } catch (error) {
          failed.push(`${rcMapParams[role]}: ${errorText(error)}`)
        }
      }
      const mapped = [...new Set(rcRoles.map(role => Number(next.mapping[role])))]
      for (const channel of mapped) {
        ensureRcCalibrationForDraft(next, channel)
        const fields = [
          ['min', `RC${channel}_MIN`], ['trim', `RC${channel}_TRIM`], ['max', `RC${channel}_MAX`],
          ['reverse', `RC${channel}_REV`],
        ] as const
        for (const [field, name] of fields) {
          try {
            const result = await px4Api.getParameter(name)
            const numeric = Number(result.value)
            if (field === 'reverse') next.channels[channel].reverse = numeric < 0 ? -1 : 1
            else if (field === 'min') next.channels[channel].min = numeric
            else if (field === 'trim') next.channels[channel].trim = numeric
            else if (field === 'max') next.channels[channel].max = numeric
          } catch (error) {
            failed.push(`${name}: ${errorText(error)}`)
          }
        }
      }
      rcDraft.value = cloneRcDraft(next)
      rcBaselineFlat.value = flattenRcDraft(next)
      rcLoadedOnce.value = true
      rcMessageLevel.value = failed.length ? 'warn' : 'success'
      rcMessage.value = failed.length
        ? `已读取主遥控映射与大部分校准参数；${failed.length} 项在当前固件中未成功读取。`
        : '已从 PX4 读取遥控通道映射与校准参数。'
      appendLog('读取 PX4 遥控参数', rcMessage.value, failed.length ? 'warn' : 'success')
      if (hasLiveRcInput.value) rcVirtualMode.value = false
    } else {
      const next = defaultRcDraft(18)
      if (trainingHasInjection('rc_roll_reverse')) next.channels[1].reverse = -1
      if (trainingHasInjection('rc_mapping_swap')) {
        next.mapping.roll = 2
        next.mapping.pitch = 1
      }
      rcDraft.value = cloneRcDraft(next)
      rcBaselineFlat.value = flattenRcDraft(next)
      rcLoadedOnce.value = true
      rcVirtualMode.value = true
      rcMessageLevel.value = trainingHasInjection('rc_roll_reverse') || trainingHasInjection('rc_mapping_swap') ? 'warn' : 'info'
      rcMessage.value = trainingHasInjection('rc_roll_reverse') || trainingHasInjection('rc_mapping_swap')
        ? '已重新载入当前案例的遥控教学异常。'
        : '已载入虚拟遥控教学配置。'
      appendLog('载入遥控教学配置', rcMessage.value, rcMessageLevel.value === 'warn' ? 'warn' : 'info')
    }
  } catch (error) {
    rcMessageLevel.value = 'error'
    rcMessage.value = errorText(error)
    appendLog('遥控参数读取失败', rcMessage.value, 'error')
  } finally {
    rcBusy.value = false
  }
}

function ensureRcCalibrationForDraft(draft: RcDraft, channel: number): void {
  if (!Number.isInteger(channel) || channel < 0 || channel > 18) return
  if (draft.channels[channel]) return
  draft.channels[channel] = { min: 1000, trim: 1500, max: 2000, reverse: 1, deadzone: 10 }
}

async function applyRcParameters(): Promise<void> {
  if (rcBusy.value) return
  if (rcValidationErrors.value.length > 0) {
    rcMessageLevel.value = 'error'
    rcMessage.value = '存在遥控映射或校准错误，请先处理红色问题。'
    return
  }
  const keys = rcDirtyKeys.value
  if (!keys.length) {
    rcMessageLevel.value = 'info'
    rcMessage.value = '当前没有待应用的遥控参数修改。'
    return
  }
  rcBusy.value = true
  try {
    if (bridgeMode.value === 'live') {
      if (px4Armed.value) throw new Error('飞机已解锁，遥控校准参数禁止写入。请先上锁。')
      const flat = flattenRcDraft(rcDraft.value)
      for (const key of keys) await px4Api.setParameter(key, Number(flat[key]))
      rcBaselineFlat.value = flattenRcDraft(rcDraft.value)
      rcMessageLevel.value = 'success'
      rcMessage.value = `已向 PX4 写入 ${keys.length} 项遥控映射/校准参数，并收到 PARAM_VALUE 回读。`
      appendLog('应用 PX4 遥控参数', keys.join('、'), 'success')
      await pollPx4()
    } else {
      await new Promise(resolve => window.setTimeout(resolve, 250))
      rcBaselineFlat.value = flattenRcDraft(rcDraft.value)
      rcMessageLevel.value = 'success'
      rcMessage.value = '教学模拟遥控配置已应用。'
      appendLog('应用遥控教学配置', rcMessage.value, 'success')
    }
  } catch (error) {
    rcMessageLevel.value = 'error'
    rcMessage.value = errorText(error)
    appendLog('遥控参数应用失败', rcMessage.value, 'error')
  } finally {
    rcBusy.value = false
  }
}

async function verifyRcSystem(): Promise<void> {
  if (rcBusy.value) return
  rcBusy.value = true
  try {
    const issues = rcValidationIssues.value
    if (issues.some(issue => issue.level === 'error')) {
      rcMessageLevel.value = 'error'
      rcMessage.value = `遥控系统检查发现 ${rcValidationErrors.value.length} 项配置错误。`
      rcVerificationPassed.value = false
      appendLog('遥控系统检查未通过', rcMessage.value, 'error')
      return
    }
    if (bridgeMode.value === 'live' && !hasLiveRcInput.value && !rcVirtualMode.value) {
      rcMessageLevel.value = 'warn'
      rcMessage.value = 'PX4 已连接，但没有收到实时 RC_CHANNELS；请检查接收机或切换虚拟教学输入。'
      rcVerificationPassed.value = false
      appendLog('遥控输入缺失', rcMessage.value, 'warn')
      return
    }
    rcMessageLevel.value = issues.length ? 'warn' : 'success'
    rcMessage.value = issues.length
      ? `遥控系统基本可用，但仍有 ${issues.length} 项校准提醒。`
      : '遥控映射、行程、方向参数检查通过。'
    rcVerificationPassed.value = true
    appendLog('遥控系统检查完成', rcMessage.value, issues.length ? 'warn' : 'success')
  } finally {
    rcBusy.value = false
  }
}

function markSafetyDirty(key: SafetyParamKey): void {
  safetyVerificationPassed.value = false
  invalidatePreflightPermit()
  const current = Number(safetyDraft.value[key])
  const baseline = Number(safetyBaseline.value[key])
  safetyDirty.value = {
    ...safetyDirty.value,
    [key]: !Number.isFinite(current) || Math.abs(current - baseline) > 1e-6,
  }
}

function safetyPctValue(key: 'BAT_LOW_THR' | 'BAT_CRIT_THR' | 'BAT_EMERGEN_THR' | 'COM_ARM_BAT_MIN'): number {
  const value = Number(safetyDraft.value[key])
  return Number.isFinite(value) ? Math.round(value * 1000) / 10 : 0
}

function setSafetyPercent(
  key: 'BAT_LOW_THR' | 'BAT_CRIT_THR' | 'BAT_EMERGEN_THR' | 'COM_ARM_BAT_MIN',
  event: Event,
): void {
  const raw = Number((event.target as HTMLInputElement).value)
  safetyDraft.value[key] = Math.max(0, Math.min(.9, raw / 100))
  markSafetyDirty(key)
}

function safetyPercent(value: number): string {
  const normalized = Math.max(0, Math.min(.5, Number(value) || 0))
  return `${(normalized / .5) * 100}%`
}

function demoSafetyProfile(): SafetyDraft {
  if ((scenario.value === 'failsafe' || trainingHasInjection('failsafe_profile')) && !demoFailsafeRepaired.value) return { ...unsafeDemoSafetyProfile }
  return { ...recommendedSafetyProfile }
}

async function loadSafetyParameters(): Promise<void> {
  if (safetyBusy.value) return
  safetyBusy.value = true
  safetyMessage.value = ''
  try {
    if (bridgeMode.value === 'live') {
      const next: SafetyDraft = { ...safetyDraft.value }
      let loaded = 0
      const failed: string[] = []
      // PARAM_VALUE uses one shared MAVLink channel. Read sequentially to avoid
      // concurrent browser requests competing for pymavlink's send buffer.
      for (const key of safetyParamKeys) {
        try {
          const result = await px4Api.getParameter(key)
          next[key] = Number(result.value)
          loaded += 1
        } catch (error) {
          failed.push(`${key}: ${errorText(error)}`)
        }
      }
      if (loaded === 0) throw new Error(failed[0] || '没有读取到安全参数')
      safetyDraft.value = next
      safetyBaseline.value = { ...next }
      safetyDirty.value = {}
      safetyLoadedOnce.value = true
      safetyMessageLevel.value = failed.length ? 'warn' : 'success'
      safetyMessage.value = failed.length
        ? `已从 PX4 读取 ${loaded}/${safetyParamKeys.length} 项参数；部分参数在当前固件中不可用。`
        : `已从 PX4 读取 ${loaded} 项安全参数。`
      appendLog('读取 PX4 安全参数', safetyMessage.value, failed.length ? 'warn' : 'success')
    } else {
      const profile = demoSafetyProfile()
      safetyDraft.value = { ...profile }
      safetyBaseline.value = { ...profile }
      safetyDirty.value = {}
      safetyLoadedOnce.value = true
      safetyMessageLevel.value = 'info'
      safetyMessage.value = scenario.value === 'failsafe' && !demoFailsafeRepaired.value
        ? '已载入 Failsafe 异常教学配置，请根据策略检查定位风险。'
        : '已载入教学模拟安全参数。'
      appendLog('载入安全设置', safetyMessage.value, scenario.value === 'failsafe' ? 'warn' : 'info')
    }
  } catch (error) {
    safetyMessageLevel.value = 'error'
    safetyMessage.value = errorText(error)
    appendLog('安全参数读取失败', safetyMessage.value, 'error')
  } finally {
    safetyBusy.value = false
  }
}

function loadRecommendedSafetyProfile(): void {
  const next = { ...recommendedSafetyProfile }
  safetyDraft.value = next
  const dirty: Partial<Record<SafetyParamKey, boolean>> = {}
  for (const key of safetyParamKeys) {
    dirty[key] = Math.abs(Number(next[key]) - Number(safetyBaseline.value[key])) > 1e-6
  }
  safetyDirty.value = dirty
  safetyMessageLevel.value = 'info'
  safetyMessage.value = `已载入教学推荐值，${safetyDirtyCount.value} 项等待应用；尚未写入 PX4。`
  appendLog('载入教学推荐安全策略', '仅更新本地草稿，等待检查后统一应用。', 'info')
}

async function applySafetyParameters(): Promise<void> {
  if (safetyBusy.value) return
  if (safetyValidationErrors.value.length > 0) {
    safetyMessageLevel.value = 'error'
    safetyMessage.value = '存在配置冲突，请先处理红色错误项。'
    return
  }
  const changed = safetyParamKeys.filter(key => safetyDirty.value[key])
  if (changed.length === 0) {
    safetyMessageLevel.value = 'info'
    safetyMessage.value = '当前没有待应用的参数修改。'
    return
  }

  safetyBusy.value = true
  safetyMessage.value = ''
  try {
    if (bridgeMode.value === 'live') {
      if (px4Armed.value) throw new Error('飞机已解锁，安全设置页面禁止写入参数。请先上锁。')
      const applied: string[] = []
      for (const key of changed) {
        const result = await px4Api.setParameter(key, Number(safetyDraft.value[key]))
        safetyDraft.value[key] = Number(result.value)
        applied.push(key)
      }
      safetyBaseline.value = { ...safetyDraft.value }
      safetyDirty.value = {}
      safetyMessageLevel.value = 'success'
      safetyMessage.value = `已向 PX4 写入 ${applied.length} 项安全参数，并收到 PARAM_VALUE 回读。`
      appendLog('应用 PX4 安全参数', applied.join('、'), 'success')
      await pollPx4()
    } else {
      await new Promise(resolve => window.setTimeout(resolve, 350))
      safetyBaseline.value = { ...safetyDraft.value }
      safetyDirty.value = {}
      if (scenario.value === 'failsafe' || trainingHasInjection('failsafe_profile')) demoFailsafeRepaired.value = true
      safetyMessageLevel.value = 'success'
      safetyMessage.value = scenario.value === 'failsafe'
        ? 'Failsafe 教学故障已修复：推荐策略已应用到模拟配置。'
        : '教学模拟安全配置已应用。'
      appendLog('应用安全设置', safetyMessage.value, 'success')
    }
  } catch (error) {
    safetyMessageLevel.value = 'error'
    safetyMessage.value = errorText(error)
    appendLog('安全参数应用失败', safetyMessage.value, 'error')
  } finally {
    safetyBusy.value = false
  }
}

async function verifySafetyConfiguration(): Promise<void> {
  if (safetyBusy.value) return
  safetyBusy.value = true
  safetyMessage.value = ''
  try {
    if (safetyValidationErrors.value.length > 0) {
      safetyMessageLevel.value = 'error'
      safetyMessage.value = `配置检查发现 ${safetyValidationErrors.value.length} 项冲突，未执行后续验证。`
      safetyVerificationPassed.value = false
      appendLog('安全策略检查未通过', safetyMessage.value, 'error')
      return
    }

    if (bridgeMode.value === 'live') {
      await px4Api.prearmCheck()
      await new Promise(resolve => window.setTimeout(resolve, 300))
      await pollPx4()
      safetyMessageLevel.value = prearmPassed.value ? (safetyValidationIssues.value.length ? 'warn' : 'success') : 'warn'
      safetyMessage.value = prearmPassed.value
        ? (safetyValidationIssues.value.length
          ? `PX4 Pre-Arm 未报告阻断，但还有 ${safetyValidationIssues.value.length} 项策略提醒。`
          : '安全策略检查与 PX4 Pre-Arm 当前均通过。')
        : `PX4 Pre-Arm 尚未通过：${liveTelemetry.value?.statustext || '请检查实时状态。'}`
      safetyVerificationPassed.value = prearmPassed.value && safetyValidationErrors.value.length === 0
      appendLog('运行安全 / Pre-Arm 验证', safetyMessage.value, safetyVerificationPassed.value ? 'success' : 'warn')
    } else {
      await new Promise(resolve => window.setTimeout(resolve, 300))
      const clean = safetyValidationIssues.value.length === 0
      safetyMessageLevel.value = clean ? 'success' : 'warn'
      safetyMessage.value = clean
        ? '教学安全策略检查通过，可进入起飞前检查。'
        : `教学策略检查完成：仍有 ${safetyValidationIssues.value.length} 项提醒。`
      safetyVerificationPassed.value = clean
      appendLog('教学安全策略验证', safetyMessage.value, clean ? 'success' : 'warn')
    }
  } catch (error) {
    safetyVerificationPassed.value = false
    safetyMessageLevel.value = 'error'
    safetyMessage.value = errorText(error)
    appendLog('安全验证失败', safetyMessage.value, 'error')
  } finally {
    safetyBusy.value = false
  }
}

async function testMotor(command: MotorName): Promise<void> {
  if (motorTestBusy.value) return
  motorTestBusy.value = true
  commandedMotor.value = command

  if (bridgeMode.value === 'live' && !trainingHasInjection('motor_mapping')) {
    actualMotor.value = command
    const outputs: MotorVector = [0, 0, 0, 0]
    outputs[motorIndex[command]] = .25
    motorOutputs.value = outputs
    appendLog(`执行 ${command} PX4 单电机测试`, '发送 MAV_CMD_ACTUATOR_TEST，输出 25%', 'info')
    try {
      await px4Api.testMotor(command, .25, 1.5)
      motorVerified.value = { ...motorVerified.value, [command]: true }
      invalidatePreflightPermit()
      appendLog(`${command} 测试指令已接受`, 'PX4 执行机构测试由 SIH 飞控实际处理', 'success')
    } catch (error) {
      appendLog(`${command} 测试失败`, errorText(error), 'error')
    }
  } else {
    const actual = resolveMotorResponse(scenario.value, mappingRepaired.value, command)
    actualMotor.value = actual
    const outputs: MotorVector = [0, 0, 0, 0]
    outputs[motorIndex[actual]] = .62
    motorOutputs.value = outputs
    appendLog(`执行 ${command} 单电机测试`, trainingHasInjection('motor_mapping') && bridgeMode.value === 'live' ? `案例使用教学映射注入，不向真实 PX4 发送执行机构指令（${command} 62%）` : `发送 ${command} 教学测试指令（62%）`, 'info')
    if (actual !== command) {
      motorVerified.value = { ...motorVerified.value, [command]: false }
      invalidatePreflightPermit()
      appendLog(`检测到 ${actual} 异常响应`, `${command} 指令触发后，实际 ${actual} 数字旋翼转动`, 'error')
    } else {
      motorVerified.value = { ...motorVerified.value, [command]: true }
      invalidatePreflightPermit()
      appendLog(`${command} 响应正确`, `${command} 编号与当前映射一致`, 'success')
    }
  }

  if (stopTimer) window.clearTimeout(stopTimer)
  stopTimer = window.setTimeout(() => {
    motorOutputs.value = [0, 0, 0, 0]
    actualMotor.value = null
    motorTestBusy.value = false
  }, 1800)
}

function stopAllMotors(): void {
  if (stopTimer) window.clearTimeout(stopTimer)
  motorOutputs.value = [0, 0, 0, 0]
  actualMotor.value = null
  motorTestBusy.value = false
}

function repairMotorMapping(): void {
  if (bridgeMode.value === 'live' && !trainingHasInjection('motor_mapping')) {
    appendLog('真实 PX4 模式', 'V1 不在前端伪造映射修复；后续将通过输出函数参数完成。', 'warn')
    return
  }
  mappingRepaired.value = true
  stopAllMotors()
  appendLog('学生修改电机映射参数', '将 M1–M4 映射恢复为理论顺序', 'warn')
  window.setTimeout(() => {
    commandedMotor.value = 'M1'
    actualMotor.value = 'M1'
    motorVerified.value = { ...motorVerified.value, M1: true }
    invalidatePreflightPermit()
    motorOutputs.value = [.45, 0, 0, 0]
    appendLog('二次测试通过', 'M1 响应正常，电机映射恢复正确', 'success')
    stopTimer = window.setTimeout(() => {
      motorOutputs.value = [0, 0, 0, 0]
      actualMotor.value = null
    }, 1400)
  }, 300)
}

function restorePreflightVerification(snapshot: PreflightSnapshot | null): void {
  if (!snapshot) return
  const passed = new Set(snapshot.checks.filter(item => item.state === 'pass').map(item => item.key))
  sensorVerificationPassed.value = passed.has('sensors')
  rcVerificationPassed.value = passed.has('rc')
  safetyVerificationPassed.value = passed.has('safety')
  if (passed.has('power')) motorVerified.value = { M1: true, M2: true, M3: true, M4: true }
}

function invalidatePreflightPermit(): void {
  if (preflightSnapshot.value) {
    clearPreflightSnapshot(assemblyStore.activeAircraftId)
    preflightSnapshot.value = null
  }
}

async function runFinalPreflight(): Promise<void> {
  if (preflightBusy.value) return
  preflightBusy.value = true
  preflightMessage.value = ''
  invalidatePreflightPermit()
  try {
    if (bridgeMode.value === 'live') {
      await px4Api.prearmCheck()
      await new Promise(resolve => window.setTimeout(resolve, 300))
      await pollPx4()
      await nextTick()
    }
    if (!preflightReady.value) {
      preflightMessage.value = `最终检查未通过：仍有 ${preflightBlockers.value.length} 项阻断。`
      appendLog('最终起飞检查未通过', preflightBlockers.value.map(item => item.title).join('、'), 'error')
      return
    }
    const snapshot: PreflightSnapshot = {
      version: 1,
      aircraft_id: assemblyStore.activeAircraftId ?? null,
      aircraft_fingerprint: aircraftFingerprint(assemblyStore.aircraft),
      passed: true,
      score: preflightScoreValue.value,
      checked_at: new Date().toISOString(),
      bridge_mode: bridgeMode.value,
      scenario: scenario.value,
      checks: preflightChecks.value.map(({ key, title, state, summary }) => ({ key, title, state, summary })),
    }
    savePreflightSnapshot(snapshot)
    preflightSnapshot.value = snapshot
    preflightMessage.value = '六项起飞门禁全部通过，已生成当前飞机的飞行许可。'
    appendLog('最终起飞检查通过', `飞行许可已生成 · ${preflightScoreValue.value}/100`, 'success')
  } catch (error) {
    preflightMessage.value = errorText(error)
    appendLog('最终起飞检查失败', preflightMessage.value, 'error')
  } finally {
    preflightBusy.value = false
  }
}

function saveDebugReport(): void {
  const report = {
    generated_at: new Date().toISOString(),
    aircraft: assemblyStore.aircraftName,
    scenario: scenario.value,
    bridge_mode: bridgeMode.value,
    px4: liveTelemetry.value,
    score: score.value,
    engineering: assemblyStore.engineering,
    rc: {
      input_source: rcInputSourceText.value,
      live_rc: liveTelemetry.value?.rc ?? null,
      parameters: flattenRcDraft(rcDraft.value),
      pending_changes: rcDirtyKeys.value,
      score: rcScore.value,
      issues: rcValidationIssues.value,
    },
    safety: {
      parameters: safetyDraft.value,
      pending_changes: safetyParamKeys.filter(key => safetyDirty.value[key]),
      score: safetyScore.value,
      issues: safetyValidationIssues.value,
    },
    preflight: {
      ready: preflightReady.value,
      score: preflightScoreValue.value,
      permit: preflightSnapshot.value,
      checks: preflightChecks.value,
    },
    training: activeTrainingCase.value ? {
      case: {
        id: activeTrainingCase.value.id,
        title: activeTrainingCase.value.title,
        category: activeTrainingCase.value.category,
        difficulty: activeTrainingCase.value.difficulty,
        recommended_minutes: activeTrainingCase.value.recommended_minutes,
        fault_source: activeTrainingCase.value.fault_source,
      },
      elapsed_seconds: trainingElapsedSeconds.value,
      hints_used: trainingHintsUsed.value,
      wrong_operations: trainingWrongOperations.value,
      visited_sections: trainingVisitedSections.value,
      evaluation: trainingEvaluationPreview.value,
    } : null,
    logs: logs.value,
  }
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `uav-debug-${assemblyStore.activeAircraftId ?? 'aircraft'}-${Date.now()}.json`
  anchor.click()
  URL.revokeObjectURL(url)
  appendLog('保存调试记录', '已生成包含 PX4 遥测的调试 JSON 报告', 'success')
}


watch(activeSection, next => {
  if (activeTrainingCase.value && !trainingVisitedSections.value.includes(next)) {
    trainingVisitedSections.value = [...trainingVisitedSections.value, next]
    scheduleTrainingProgressSync()
  }
  if (next === 'safety' && !safetyLoadedOnce.value) void loadSafetyParameters()
  if (next === 'rc' && !rcLoadedOnce.value) void loadRcParameters()
})

watch(() => route.query.section, value => {
  const section = Array.isArray(value) ? value[0] : value
  if (section && steps.some(item => item.key === section)) activeSection.value = section as SectionKey
})

watch(currentRcChannels, values => updateRcCapture(values), { deep: true })

watch([trainingHintsUsed, trainingWrongOperations], () => scheduleTrainingProgressSync())
watch(trainingConditionState, () => scheduleTrainingProgressSync(), { deep: true })
watch(preflightPermitValid, () => scheduleTrainingProgressSync())

watch(rcDirtyCount, count => {
  if (count > 0) { rcVerificationPassed.value = false; invalidatePreflightPermit() }
})
watch(safetyDirtyCount, count => {
  if (count > 0) { safetyVerificationPassed.value = false; invalidatePreflightPermit() }
})
watch(() => assemblyStore.activeAircraftId, () => {
  sensorVerificationPassed.value = false
  rcVerificationPassed.value = false
  safetyVerificationPassed.value = false
  motorVerified.value = { M1: false, M2: false, M3: false, M4: false }
  preflightSnapshot.value = loadPreflightSnapshot(assemblyStore.activeAircraftId, aircraftFingerprint(assemblyStore.aircraft))
  restorePreflightVerification(preflightSnapshot.value)
})

watch(bridgeMode, (next, previous) => {
  if (next !== previous) {
    invalidatePreflightPermit()
    sensorVerificationPassed.value = false
    rcVerificationPassed.value = false
    safetyVerificationPassed.value = false
    motorVerified.value = { M1: false, M2: false, M3: false, M4: false }
  }
  if (next !== previous && activeSection.value === 'safety' && safetyDirtyCount.value === 0) {
    safetyLoadedOnce.value = false
    void loadSafetyParameters()
  }
  if (next !== previous && activeSection.value === 'rc' && rcDirtyCount.value === 0) {
    rcLoadedOnce.value = false
    void loadRcParameters()
  }
})

onMounted(async () => {
  await auth.initialize()
  await assemblyStore.initialize()
  const requestedSection = Array.isArray(route.query.section) ? route.query.section[0] : route.query.section
  if (requestedSection && steps.some(item => item.key === requestedSection)) activeSection.value = requestedSection as SectionKey
  try {
    trainingCases.value = await loadFaultTrainingCases()
    trainingCatalogError.value = ''
    if (assignedScenarioId.value) {
      const assignedCase = trainingCases.value.find(item => item.id === assignedScenarioId.value)
      if (assignedCase) startTrainingCase(assignedCase)
      else trainingCatalogError.value = `教师任务指定的案例 ${assignedScenarioId.value} 不在当前案例库中。`
    }
  } catch (error) {
    trainingCatalogError.value = errorText(error)
  }
  preflightSnapshot.value = loadPreflightSnapshot(assemblyStore.activeAircraftId, aircraftFingerprint(assemblyStore.aircraft))
  restorePreflightVerification(preflightSnapshot.value)
  timer = window.setInterval(() => { clockTick.value += 1 }, 100)
  px4PollTimer = window.setInterval(() => { void pollPx4() }, 300)
  appendLog('进入动力系统调试', '优先探测真实 PX4 Bridge；未连接时保留教学模拟。', 'info')
  if (scenario.value === 'mapping') {
    appendLog('载入电机映射故障', '仅在教学模拟模式将 M1 指令映射到 M3', 'warn')
  }
  await pollPx4()
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
  if (px4PollTimer) window.clearInterval(px4PollTimer)
  if (stopTimer) window.clearTimeout(stopTimer)
  if (trainingSyncTimer) window.clearTimeout(trainingSyncTimer)
})
</script>


<style scoped>
.debug-page {
  --bg:#071321;
  --panel:#0b1b2b;
  --panel2:#0d2134;
  --line:rgba(99, 145, 186, .22);
  --line-strong:rgba(67, 170, 244, .4);
  --text:#d9e8f6;
  --muted:#7897b5;
  --blue:#28a8ff;
  --cyan:#55d9ff;
  --green:#48df8b;
  --red:#ff5e57;
  --amber:#f0bd45;
  display:grid;
  grid-template-columns: 258px minmax(700px, 1fr) 420px;
  gap:0;
  height:calc(100vh - 58px);
  min-height:720px;
  overflow:hidden;
  background:
    radial-gradient(circle at 50% 20%, rgba(31, 103, 154, .12), transparent 35%),
    linear-gradient(180deg, #081523, #06111e);
  color:var(--text);
}
button, a { font:inherit; }
.debug-sidebar, .debug-rightbar { background:rgba(6, 18, 31, .88); }
.debug-sidebar { position:relative; overflow:auto; border-right:1px solid var(--line); padding:16px 14px 72px; }
.debug-main { min-width:0; overflow:auto; padding:16px 12px 22px; }
.debug-rightbar { overflow:auto; border-left:1px solid var(--line); padding:16px 14px; }
.side-section + .side-section { margin-top:18px; padding-top:15px; border-top:1px solid rgba(102,147,188,.14); }
.side-title { margin:0 6px 10px; color:#dbeeff; font-size:13px; font-weight:800; letter-spacing:.03em; }
.flow-step, .scenario-card { width:100%; border:1px solid transparent; background:transparent; color:var(--text); cursor:pointer; }
.flow-step { display:grid; grid-template-columns:30px 34px 1fr; align-items:center; min-height:66px; padding:7px 8px; border-radius:9px; text-align:left; position:relative; }
.flow-step:not(:last-child)::after { content:""; position:absolute; left:22px; top:52px; width:1px; height:28px; border-left:1px dashed rgba(72, 139, 190, .38); }
.flow-step:hover { background:rgba(46, 139, 202, .08); }
.flow-step.active { border-color:rgba(47,171,255,.46); background:linear-gradient(90deg, rgba(23,126,198,.2), rgba(18,57,91,.2)); box-shadow:inset 3px 0 #2aa8ff; }
.step-no { width:22px;height:22px;display:grid;place-items:center;border-radius:50%;border:1px solid rgba(57,164,238,.6);color:#9edcff;background:#102c43;font-size:10px; }
.step-icon { font-size:22px;color:#b8ddf6; }
.step-copy { display:grid;gap:2px; }
.step-copy b { font-size:12px; }
.step-copy small { color:var(--muted);font-size:9px; }
.scenario-card { display:flex;align-items:center;gap:10px;padding:10px;border-radius:8px;text-align:left;border-color:rgba(105,149,186,.13);background:rgba(255,255,255,.018);margin-bottom:7px; }
.scenario-card > span { width:26px;color:#b9d6ed;font-size:18px; }
.scenario-card div { display:grid;gap:2px; }
.scenario-card b { font-size:11px; }
.scenario-card small { font-size:8px;color:var(--muted); }
.scenario-card.active { border-color:#258fd3;background:rgba(17,109,171,.22);box-shadow:0 0 18px rgba(21,132,205,.14); }
.practice-mark { position:absolute;left:20px;bottom:18px;display:grid;color:#506f8b;letter-spacing:.12em;font-size:9px; }
.practice-mark span { font-size:7px; }
.section-tabs { height:44px;display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:8px;background:rgba(8,24,39,.72);margin-bottom:12px;overflow:hidden; }
.section-tabs button { position:relative;border:0;border-right:1px solid rgba(90,140,180,.18);background:transparent;color:#8ca8c0;cursor:pointer;font-size:11px; }
.section-tabs button.active { color:#43c1ff;background:linear-gradient(180deg,rgba(17,93,145,.1),rgba(17,93,145,.04)); }
.section-tabs button.active::after { content:"";position:absolute;left:14%;right:14%;bottom:0;height:2px;background:#26b2ff;box-shadow:0 0 8px #26b2ff; }
.sensor-workbench { display:grid;gap:12px; }
.sensor-hero-surface { overflow:hidden; }
.sensor-hero-grid { display:grid;grid-template-columns:minmax(300px,.82fr) minmax(420px,1.3fr);gap:16px;padding:16px; }
.attitude-panel { display:grid;grid-template-columns:210px 1fr;gap:16px;align-items:center; }
.attitude-shell { position:relative;width:210px;height:210px;border-radius:50%;overflow:hidden;border:2px solid rgba(90,180,240,.52);background:#0b2237;box-shadow:0 0 0 8px rgba(6,18,31,.82),0 0 28px rgba(37,154,226,.18),inset 0 0 30px rgba(0,0,0,.45); }
.attitude-moving { position:absolute;left:-25%;top:-25%;width:150%;height:150%;transform-origin:50% 50%;transition:transform .12s linear; }
.attitude-sky,.attitude-ground { position:absolute;left:0;width:100%;height:50%; }
.attitude-sky { top:0;background:linear-gradient(180deg,#1c75a9,#246da0 64%,#2f89ba); }
.attitude-ground { bottom:0;background:linear-gradient(180deg,#7b5735,#513a28 60%,#35271d); }
.attitude-horizon { position:absolute;left:0;top:50%;width:100%;height:2px;background:#f4f7fb;box-shadow:0 0 8px rgba(255,255,255,.55); }
.attitude-aircraft { position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);display:grid;grid-template-columns:44px 10px 44px;align-items:center;gap:4px;z-index:4; }
.attitude-aircraft i { height:4px;background:#ffd65a;border-radius:4px;box-shadow:0 0 5px rgba(255,214,90,.5); }
.attitude-aircraft span { width:10px;height:10px;border:3px solid #ffd65a;border-radius:50%;box-sizing:border-box; }
.attitude-pitch-mark { position:absolute;left:50%;transform:translateX(-50%);z-index:3;font-size:8px;color:rgba(255,255,255,.78);text-shadow:0 1px 2px #000; }
.pitch-plus { top:27%; }.pitch-zero { top:48%; }.pitch-minus { top:69%; }
.attitude-heading { position:absolute;bottom:14px;left:50%;transform:translateX(-50%);padding:4px 8px;border-radius:4px;background:rgba(2,12,22,.72);color:#dff4ff;font-size:10px;letter-spacing:.08em;z-index:5; }
.attitude-readouts { display:grid;gap:9px; }
.attitude-readouts > div { min-height:50px;display:grid;align-content:center;gap:3px;padding:8px 10px;border:1px solid rgba(92,145,185,.18);border-radius:7px;background:rgba(7,25,40,.66); }
.attitude-readouts span { color:#708fa9;font-size:8px;letter-spacing:.08em; }.attitude-readouts b { color:#d9f1ff;font-size:16px; }
.fc-overview { display:grid;grid-template-rows:auto 1fr;gap:12px;min-width:0; }
.fc-status-row { display:grid;grid-template-columns:repeat(4,1fr);gap:8px; }
.fc-chip { min-height:58px;display:grid;align-content:center;gap:4px;padding:8px 10px;border:1px solid rgba(89,145,188,.17);border-radius:7px;background:rgba(6,24,39,.66); }
.fc-chip span { color:#708fa9;font-size:8px; }.fc-chip b { color:#d6ecfb;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.imu-block { border:1px solid rgba(91,145,187,.16);border-radius:8px;background:rgba(6,23,37,.58);overflow:hidden; }
.sensor-block-title,.sensor-card-head { display:flex;align-items:center;justify-content:space-between;gap:10px; }
.sensor-block-title { padding:10px 12px;border-bottom:1px solid rgba(84,137,178,.14); }.sensor-block-title > div { display:grid;gap:2px; }.sensor-block-title b { font-size:11px; }.sensor-block-title small { color:#6787a2;font-size:7px; }
.sensor-status-pill { display:inline-flex;align-items:center;justify-content:center;min-width:54px;height:22px;padding:0 7px;border-radius:999px;border:1px solid rgba(113,150,180,.24);background:rgba(95,127,150,.08);color:#839eb3;font-size:8px;font-weight:700; }
.sensor-status-pill.ok { border-color:rgba(66,218,134,.35);background:rgba(37,129,79,.15);color:#5de39a; }.sensor-status-pill.warn { border-color:rgba(255,101,91,.4);background:rgba(134,43,38,.18);color:#ff857e; }.sensor-status-pill.unknown { color:#9eafbc;border-color:rgba(154,174,190,.25); }
.vector-table { padding:7px 11px; }.vector-head,.vector-row { display:grid;grid-template-columns:54px 1fr 1fr;align-items:center;min-height:31px;border-bottom:1px solid rgba(82,129,165,.1);font-size:9px; }.vector-head { color:#6c89a2;font-size:8px; }.vector-row b { color:#50c8ff; }.vector-row span { color:#c7dfef;font-variant-numeric:tabular-nums; }
.imu-footer { display:flex;gap:20px;padding:8px 11px;background:rgba(7,22,35,.55);color:#7894ad;font-size:8px; }.imu-footer b { color:#bfdaeb; }
.sensor-card-grid { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px; }
.sensor-card { min-height:210px;padding:12px;transition:border-color .18s,box-shadow .18s; }.sensor-card-fault { border-color:rgba(255,87,76,.44);box-shadow:0 0 20px rgba(180,48,42,.12); }
.sensor-card-head { padding-bottom:10px;border-bottom:1px solid rgba(87,139,178,.13); }.sensor-card-head > div { display:flex;align-items:center;gap:8px; }.sensor-card-head b { font-size:11px; }.sensor-card-icon { color:#46bfff;font-size:18px; }
.sensor-kpi-row { display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0; }.sensor-kpi-row > div { display:grid;gap:3px;padding:8px;border:1px solid rgba(87,139,178,.13);border-radius:6px;background:rgba(5,21,34,.5); }.sensor-kpi-row span { color:#6f8da7;font-size:8px; }.sensor-kpi-row b { color:#d8edfb;font-size:13px; }
.sensor-detail-list { display:grid;gap:6px;margin:0; }.sensor-detail-list > div { display:flex;justify-content:space-between;gap:8px;padding:4px 2px;border-bottom:1px dashed rgba(86,130,164,.1); }.sensor-detail-list dt { color:#708ca4;font-size:8px; }.sensor-detail-list dd { margin:0;color:#bdd6e8;font-size:9px;font-variant-numeric:tabular-nums; }
.compass-display { display:grid;grid-template-columns:124px 1fr;gap:16px;align-items:center;padding:12px 4px 6px; }.compass-ring { position:relative;width:118px;height:118px;border-radius:50%;border:1px solid rgba(78,177,235,.42);background:radial-gradient(circle,#102d45 0 42%,#081b2c 43% 100%);box-shadow:inset 0 0 18px rgba(0,0,0,.38); }.compass-ring > span { position:absolute;color:#789bb5;font-size:8px; }.compass-ring .north{top:7px;left:50%;transform:translateX(-50%);color:#ff8179}.compass-ring .east{right:9px;top:50%;transform:translateY(-50%)}.compass-ring .south{bottom:7px;left:50%;transform:translateX(-50%)}.compass-ring .west{left:9px;top:50%;transform:translateY(-50%)}
.compass-ring i { position:absolute;left:57px;top:21px;width:4px;height:38px;background:linear-gradient(180deg,#ff675f 0 48%,#8dd7ff 49% 100%);transform-origin:50% 38px;border-radius:4px;transition:transform .14s linear;box-shadow:0 0 8px rgba(255,103,95,.25); }.compass-ring b { position:absolute;left:50%;bottom:28px;transform:translateX(-50%);font-size:13px;color:#e5f5ff; }
.mag-values { display:grid;gap:9px; }.mag-values > div { display:grid;gap:3px;padding:8px;border:1px solid rgba(84,138,177,.12);border-radius:6px;background:rgba(5,20,32,.45); }.mag-values span { color:#6f8da7;font-size:8px; }.mag-values b { color:#c9e0ef;font-size:9px;line-height:1.4; }
.inline-sensor-warning { margin-top:8px;padding:7px 8px;border:1px solid rgba(255,96,84,.33);border-radius:5px;background:rgba(120,35,31,.16);color:#ff9a93;font-size:8px; }
.large-sensor-number { display:grid;place-items:center;padding:18px 4px 14px; }.large-sensor-number b { color:#5dc8ff;font-size:28px;font-weight:700; }.large-sensor-number span { color:#6e8ba4;font-size:8px;margin-top:3px; }
.ekf-state-block { display:grid;gap:7px;margin:12px 0; }.ekf-state-block > div { display:flex;justify-content:space-between;gap:12px;padding:7px 8px;border-radius:6px;background:rgba(5,21,34,.48); }.ekf-state-block span { color:#6f8da7;font-size:8px; }.ekf-state-block b { color:#cce3f2;font-size:9px; }.ok-text{color:#5de39a!important}.warn-text{color:#ff887f!important}
.ekf-summary { padding:8px 9px;border-radius:6px;font-size:8px;line-height:1.55; }.ekf-summary.pass { color:#72dda0;background:rgba(37,120,76,.14);border:1px solid rgba(68,208,128,.2); }.ekf-summary.fail { color:#ff9690;background:rgba(121,39,35,.16);border:1px solid rgba(255,91,82,.25); }
.calibration-surface { overflow:hidden; }.sensor-diagnostic-button { border:1px solid rgba(46,168,239,.44);border-radius:5px;background:#0f5680;color:#dff5ff;padding:6px 10px;font-size:8px;cursor:pointer; }.sensor-diagnostic-button:disabled { opacity:.4;cursor:not-allowed; }
.calibration-grid { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;padding:12px; }.calibration-card { display:grid;grid-template-columns:minmax(0,1fr) 120px 90px;align-items:center;gap:10px;padding:11px;border:1px solid rgba(90,142,181,.15);border-radius:7px;background:rgba(6,23,37,.58); }.calibration-copy { display:flex;align-items:center;gap:10px;min-width:0; }.calibration-icon { width:34px;height:34px;display:grid;place-items:center;border-radius:50%;border:1px solid rgba(55,178,244,.33);background:rgba(25,119,176,.12);color:#54c9ff;font-size:18px; }.calibration-copy > div { display:grid;gap:3px;min-width:0; }.calibration-copy b { font-size:10px; }.calibration-copy small { color:#6f8ca5;font-size:7px;line-height:1.45; }
.calibration-state { display:flex;align-items:center;gap:6px;color:#7f9ab1;font-size:8px;min-width:0; }.calibration-state small { overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }.calibration-state-dot { width:7px;height:7px;border-radius:50%;background:#637c91; }.calibration-state-dot.running { background:#4cbcff;box-shadow:0 0 8px rgba(76,188,255,.55); }.calibration-state-dot.requested { background:#f1c34e;box-shadow:0 0 8px rgba(241,195,78,.45); }.calibration-state-dot.passed { background:#4bdb88;box-shadow:0 0 8px rgba(75,219,136,.45); }.calibration-state-dot.failed { background:#ff665f;box-shadow:0 0 8px rgba(255,102,95,.45); }
.calibration-card > button { min-height:34px;border:1px solid rgba(57,163,226,.34);border-radius:5px;background:#0e324d;color:#bde6ff;font-size:8px;cursor:pointer; }.calibration-card > button:hover:not(:disabled){border-color:#36baff;background:#12577f;color:white}.calibration-card > button:disabled{opacity:.38;cursor:not-allowed}
.calibration-note { margin:0 12px 12px;display:grid;grid-template-columns:72px 1fr;gap:8px;padding:8px 10px;border:1px solid rgba(77,139,181,.16);border-radius:6px;background:rgba(5,19,31,.58);font-size:8px;line-height:1.55; }.calibration-note b { color:#8fc9ed; }.calibration-note span { color:#6f8ca5; }
.power-layout { display:grid;grid-template-columns:minmax(520px,1.8fr) minmax(260px,.82fr);gap:12px; }
.surface { border:1px solid var(--line);border-radius:9px;background:linear-gradient(180deg,rgba(12,31,49,.94),rgba(8,24,39,.94));box-shadow:0 12px 30px rgba(0,0,0,.12); }
.surface-heading { height:42px;display:flex;align-items:center;justify-content:space-between;padding:0 13px;border-bottom:1px solid rgba(91,139,178,.16); }
.surface-heading > div { display:flex;align-items:center;gap:8px; }
.surface-heading b { font-size:12px; }
.heading-icon { color:#35b9ff;font-size:15px; }
.heading-note { color:#6686a2;font-size:8px; }
.scene-surface { min-width:0;overflow:hidden; }
.scene-and-controls { height:470px;display:grid;grid-template-columns:minmax(0,1fr) 126px;gap:8px;padding:8px; }
.motor-test-stack { display:flex;flex-direction:column;gap:9px;padding-top:58px; }
.motor-test, .stop-all { min-height:43px;border-radius:6px;border:1px solid rgba(92,145,185,.32);background:linear-gradient(180deg,#102a41,#0b1c2c);color:#bad5e9;cursor:pointer;font-size:10px; }
.motor-test:hover,.motor-test.active { border-color:#2dabff;background:linear-gradient(180deg,#1789d0,#116aa5);color:white;box-shadow:0 0 16px rgba(36,161,239,.25); }
.stop-all { margin-top:3px;border-color:rgba(255,88,82,.52);color:#ff807a;background:rgba(118,35,34,.16); }
.parameter-surface { padding-bottom:10px; }
.metric-grid { display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px; }
.metric-card { min-height:87px;display:grid;grid-template-columns:30px 1fr;grid-template-rows:1fr 1fr;align-items:center;padding:10px;border:1px solid rgba(91,141,180,.16);border-radius:8px;background:rgba(8,27,44,.78); }
.metric-card > span { grid-row:1/3;color:#3bb6ff;font-size:20px; }
.metric-card small { color:#7493ae;font-size:9px;align-self:end; }
.metric-card b { color:#d9efff;font-size:13px;align-self:start; }
.metric-card.good b,.metric-card.good > span { color:var(--green); }
.safety-tip { margin:3px 12px 2px;padding:8px 9px;border:1px solid rgba(87,142,184,.15);border-radius:6px;color:#6f8eaa;font-size:8px;background:rgba(7,22,36,.72); }
.lower-grid { display:grid;grid-template-columns:.92fr 1fr;gap:12px;margin-top:12px; }
.actuator-list { padding:12px;display:grid;gap:14px; }
.actuator-row { display:grid;grid-template-columns:28px 38px 1fr 42px;gap:8px;align-items:center;font-size:10px; }
.actuator-row > span { color:#7592ac; }
.actuator-row strong { font-size:11px;text-align:right; }
.output-bar { height:11px;border-radius:999px;background:#1a3249;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(93,142,180,.08); }
.output-bar i { display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#177ee8,#37c4ff);box-shadow:0 0 10px rgba(44,176,255,.28);transition:width .12s linear; }
.mapping-surface { overflow:hidden; }
table { width:calc(100% - 24px);margin:10px 12px 8px;border-collapse:collapse;font-size:9px;text-align:center; }
th,td { padding:7px 5px;border:1px solid rgba(82,132,172,.17); }
th { color:#7f9bb4;font-weight:600;background:rgba(12,35,54,.6); }
td:first-child { color:#45baff;font-weight:800; }
.response-fault { color:#ff7a72!important; }.response-ok { color:#55df91!important; }
.fault-banner,.pass-banner { margin:8px 12px 12px;min-height:47px;display:flex;align-items:center;gap:9px;padding:7px 9px;border-radius:7px;font-size:9px; }
.fault-banner { border:1px solid rgba(255,80,71,.46);background:rgba(126,34,31,.22);color:#ff9b96; }
.fault-banner > span { width:23px;height:23px;display:grid;place-items:center;border-radius:50%;background:#c4423c;color:white;font-weight:900; }
.fault-banner div { display:grid;gap:2px;flex:1; }.fault-banner small { color:#b87f7c; }
.fault-banner button { border:1px solid rgba(255,126,117,.5);border-radius:5px;background:rgba(145,48,43,.35);color:#ffd0cc;padding:6px 9px;cursor:pointer;font-size:8px; }
.pass-banner { border:1px solid rgba(66,215,134,.3);background:rgba(35,124,78,.15);color:#70e5a2; }

.safety-workbench { display:grid;gap:12px; }
.safety-summary-surface { overflow:hidden; }
.safety-summary-main { display:grid;grid-template-columns:1fr 140px;gap:18px;align-items:center;padding:18px 20px 14px; }
.safety-kicker { color:#43bdfc;font-size:7px;letter-spacing:.18em;font-weight:800; }
.safety-summary-main h2 { margin:5px 0 6px;color:#e2f4ff;font-size:20px; }
.safety-summary-main p { margin:0;max-width:720px;color:#6f8fa9;font-size:9px;line-height:1.65; }
.safety-summary-score { display:grid;place-items:end;padding-left:18px;border-left:1px solid rgba(88,141,180,.18); }
.safety-summary-score small { color:#7492ab;font-size:8px; }
.safety-summary-score b { color:#57df96;font-size:34px;line-height:1.1; }.safety-summary-score b.warn{color:#f1be57}.safety-summary-score em{font-size:12px;color:#7894aa;font-style:normal;margin-left:3px}
.safety-summary-strip { display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid rgba(88,141,180,.14);background:rgba(5,20,33,.42); }
.safety-summary-strip > div { min-height:48px;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 13px;border-right:1px solid rgba(88,141,180,.1); }
.safety-summary-strip > div:last-child{border-right:0}.safety-summary-strip span{color:#6f8da6;font-size:8px}.safety-summary-strip b{color:#cbe4f3;font-size:9px}.safety-summary-strip b.ok{color:#58df96}.safety-summary-strip b.warn{color:#f2bf58}.safety-summary-strip b.bad{color:#ff7771}
.safety-training-banner { display:flex;align-items:center;gap:10px;margin:0 12px 12px;padding:9px 11px;border:1px solid rgba(255,92,82,.37);border-radius:7px;background:rgba(125,34,31,.18); }.safety-training-banner.repaired{border-color:rgba(73,214,135,.3);background:rgba(36,119,74,.14)}
.safety-training-banner > span { width:25px;height:25px;display:grid;place-items:center;border-radius:50%;background:#d64f47;color:white;font-weight:900; }.safety-training-banner.repaired > span{background:#38bd76}
.safety-training-banner div{display:grid;gap:2px}.safety-training-banner b{color:#ff9891;font-size:9px}.safety-training-banner.repaired b{color:#67e49c}.safety-training-banner small{color:#9e7774;font-size:8px}.safety-training-banner.repaired small{color:#79a78c}
.safety-card-grid { display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px; }
.safety-config-card { overflow:hidden; }
.safety-fields { display:grid;padding:4px 12px 10px; }
.safety-field { min-height:66px;display:grid;grid-template-columns:minmax(0,1fr) 166px;gap:14px;align-items:center;padding:9px 0;border-bottom:1px solid rgba(85,136,175,.11); }
.safety-field:last-child{border-bottom:0}.safety-field > div:first-child{display:grid;grid-template-columns:auto auto;justify-content:start;gap:3px 7px}.safety-field b{font-size:9px;color:#d1e8f6}.safety-field code{align-self:center;color:#48bffb;background:rgba(33,129,184,.1);padding:2px 5px;border-radius:4px;font-size:7px}.safety-field small{grid-column:1/3;color:#6b879f;font-size:7px;line-height:1.45}
.safety-input { height:34px;display:grid;grid-template-columns:1fr 35px;border:1px solid rgba(86,142,183,.24);border-radius:6px;background:#071b2c;overflow:hidden; }.safety-input input{min-width:0;border:0;background:transparent;color:#dbf0fc;padding:0 9px;outline:none;font-size:9px}.safety-input span{display:grid;place-items:center;border-left:1px solid rgba(86,142,183,.17);color:#7895ad;font-size:8px;background:rgba(10,36,55,.75)}
.safety-field select { width:100%;height:34px;border:1px solid rgba(86,142,183,.24);border-radius:6px;background:#071b2c;color:#d0e8f6;padding:0 8px;outline:none;font-size:8px; }
.safety-field input:focus,.safety-field select:focus{border-color:#31b4fa;box-shadow:0 0 0 2px rgba(49,180,250,.07)}
.battery-threshold-visual { padding:12px 14px 2px; }.battery-scale{position:relative;height:13px;border-radius:999px;background:linear-gradient(90deg,#d94f48 0 12%,#e69c43 12% 28%,#42c97d 28% 100%);box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)}.battery-scale i{position:absolute;top:-5px;width:2px;height:23px;background:#fff;box-shadow:0 0 7px rgba(255,255,255,.5)}.battery-scale i::after{content:"";position:absolute;left:-3px;top:-2px;width:8px;height:8px;border-radius:50%;background:currentColor}.battery-scale .low{color:#f1c158}.battery-scale .critical{color:#ff8b56}.battery-scale .emergency{color:#ff5c55}.battery-scale-labels{display:flex;justify-content:space-between;margin-top:5px;color:#607e97;font-size:7px}
.geofence-preview { display:grid;grid-template-columns:128px 1fr;gap:14px;align-items:center;padding:12px 14px 4px; }.geofence-cylinder{position:relative;width:118px;height:72px;border:1px solid rgba(55,177,239,.38);border-radius:50%/24%;background:linear-gradient(180deg,rgba(32,121,172,.13),rgba(6,25,39,.1));box-shadow:inset 0 0 20px rgba(25,121,175,.08)}.geofence-cylinder::before,.geofence-cylinder::after{content:"";position:absolute;left:-1px;width:118px;height:22px;border:1px solid rgba(55,177,239,.31);border-radius:50%}.geofence-cylinder::before{top:-1px}.geofence-cylinder::after{bottom:-1px}.geofence-cylinder i{position:absolute;left:50%;top:10px;bottom:10px;border-left:1px dashed rgba(88,195,249,.34)}.gf-drone{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:#50c7ff;font-size:18px;z-index:2}.geofence-preview > div:last-child{display:grid;grid-template-columns:1fr auto;gap:6px 10px}.geofence-preview span{color:#6e8ba4;font-size:8px}.geofence-preview b{color:#c9e5f5;font-size:10px;text-align:right}
.arming-gate { display:flex;align-items:center;gap:11px;margin:12px;padding:10px;border:1px solid rgba(84,140,181,.16);border-radius:7px;background:rgba(5,20,33,.48); }.arming-gate-icon{width:34px;height:34px;display:grid;place-items:center;border-radius:50%;font-size:18px;font-weight:800}.arming-gate-icon.pass{color:#58df96;border:1px solid rgba(76,217,138,.32);background:rgba(37,124,77,.14)}.arming-gate-icon.block{color:#ff7771;border:1px solid rgba(255,96,87,.32);background:rgba(126,38,34,.16)}.arming-gate > div:last-child{display:grid;gap:3px}.arming-gate b{font-size:9px}.arming-gate small{color:#708ca5;font-size:7px;line-height:1.45}
.safety-diagnostic-surface { overflow:hidden; }.safety-check-pill{padding:4px 8px;border-radius:999px;font-size:8px;font-weight:700}.safety-check-pill.ok{color:#5ce199;border:1px solid rgba(76,219,139,.28);background:rgba(35,122,76,.14)}.safety-check-pill.warn{color:#f2bd56;border:1px solid rgba(242,189,86,.28);background:rgba(133,95,29,.13)}
.safety-diagnostic-body{display:grid;grid-template-columns:1fr 210px;gap:14px;padding:12px}.safety-issue-list{display:grid;gap:7px;align-content:start}.safety-no-issues,.safety-issue{min-height:48px;display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:7px}.safety-no-issues{border:1px solid rgba(69,210,131,.22);background:rgba(34,120,74,.12)}.safety-no-issues > span{width:24px;height:24px;display:grid;place-items:center;border-radius:50%;background:#34b86f;color:white}.safety-no-issues div,.safety-issue div{display:grid;gap:2px}.safety-no-issues b{color:#65e39a;font-size:9px}.safety-no-issues small,.safety-issue small{color:#6f8ba3;font-size:7px;line-height:1.45}
.safety-issue{border:1px solid rgba(239,185,76,.25);background:rgba(125,91,28,.11)}.safety-issue.error{border-color:rgba(255,88,78,.32);background:rgba(126,34,31,.15)}.safety-issue > span{width:24px;height:24px;display:grid;place-items:center;border-radius:50%;background:#c49336;color:white;font-weight:900}.safety-issue.error > span{background:#d14a43}.safety-issue b{color:#edc872;font-size:9px}.safety-issue.error b{color:#ff9089}
.safety-actions{display:grid;gap:8px;align-content:start}.safety-actions button{min-height:36px;border:1px solid rgba(70,153,210,.3);border-radius:6px;background:#0d2a41;color:#acd7ef;font-size:8px;cursor:pointer}.safety-actions button:hover:not(:disabled){border-color:#2fb5ff;background:#104e75;color:#fff}.safety-actions button:disabled{opacity:.38;cursor:not-allowed}.safety-actions .primary-action{border-color:#2eaef5;background:#0e6d9f;color:white}.safety-actions .verify-action{border-color:rgba(87,218,146,.34);background:rgba(25,106,65,.26);color:#81e7ad}
.safety-message{margin:0 12px 12px;padding:8px 10px;border-radius:6px;font-size:8px;line-height:1.5}.safety-message.info{border:1px solid rgba(70,158,217,.25);background:rgba(25,91,132,.12);color:#87c8ee}.safety-message.success{border:1px solid rgba(69,214,134,.25);background:rgba(34,122,74,.12);color:#6fe2a1}.safety-message.warn{border:1px solid rgba(240,187,83,.28);background:rgba(125,90,30,.12);color:#eecb7a}.safety-message.error{border:1px solid rgba(255,91,82,.3);background:rgba(126,35,31,.15);color:#ff9992}

.rc-workbench{display:grid;gap:12px}.rc-summary-surface{overflow:hidden}.rc-summary-main{display:grid;grid-template-columns:minmax(0,1fr) 150px;gap:16px;align-items:center;padding:15px 16px 12px}.rc-kicker{display:block;color:#55c8ff;font-size:7px;font-weight:800;letter-spacing:.16em;margin-bottom:5px}.rc-summary-main h2{margin:0;color:#e2f2ff;font-size:18px}.rc-summary-main p{max-width:760px;margin:6px 0 0;color:#7392ad;font-size:8px;line-height:1.65}.rc-summary-score{min-height:78px;display:grid;place-items:center;align-content:center;border:1px solid rgba(54,177,246,.26);border-radius:9px;background:linear-gradient(135deg,rgba(21,111,165,.16),rgba(8,32,49,.46));box-shadow:inset 0 0 24px rgba(34,146,215,.06)}.rc-summary-score small{color:#7597b1;font-size:8px}.rc-summary-score b{color:#67e4a4;font-size:27px;line-height:1}.rc-summary-score b.warn{color:#efbd54}.rc-summary-score em{font-size:10px;font-style:normal;color:#7898af;margin-left:2px}.rc-summary-strip{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid rgba(88,142,184,.14);background:rgba(4,18,30,.34)}.rc-summary-strip>div{min-height:55px;display:grid;align-content:center;gap:4px;padding:8px 12px;border-right:1px solid rgba(88,142,184,.11)}.rc-summary-strip>div:last-child{border-right:0}.rc-summary-strip span{color:#6c8aa4;font-size:7px}.rc-summary-strip b{color:#d2e9f8;font-size:10px}.rc-summary-strip b.ok{color:#5ce098}.rc-summary-strip b.warn{color:#f0bf58}.rc-summary-strip b.bad{color:#ff7770}.rc-no-input-banner{display:flex;align-items:center;gap:10px;margin:0 12px 12px;padding:9px 10px;border:1px solid rgba(241,183,74,.26);border-radius:7px;background:rgba(126,90,26,.12)}.rc-no-input-banner>span{width:25px;height:25px;display:grid;place-items:center;border-radius:50%;background:#b88932;color:#fff;font-weight:900}.rc-no-input-banner>div{display:grid;gap:2px}.rc-no-input-banner b{color:#e5c16f;font-size:9px}.rc-no-input-banner small{color:#8f815f;font-size:7px;line-height:1.45}
.rc-top-grid{display:grid;grid-template-columns:minmax(470px,1.2fr) minmax(280px,.8fr);gap:12px}.rc-stick-surface,.rc-channel-surface,.rc-mapping-surface,.rc-calibration-surface,.rc-failsafe-surface{overflow:hidden}.rc-source-actions{display:flex;gap:5px}.rc-source-actions button{min-height:25px;padding:0 9px;border:1px solid rgba(85,145,190,.22);border-radius:5px;background:#0a2236;color:#7898b1;font-size:7px;cursor:pointer}.rc-source-actions button.active{border-color:#28a9f8;background:rgba(21,116,176,.24);color:#78d2ff}.rc-source-actions button:disabled{opacity:.35;cursor:not-allowed}.rc-stick-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px}.stick-card{display:grid;gap:8px}.stick-title{display:flex;justify-content:space-between;align-items:center}.stick-title b{font-size:9px;color:#cfe8f7}.stick-title small{font-size:7px;color:#6686a0}.stick-pad{position:relative;height:190px;border:1px solid rgba(71,154,211,.22);border-radius:12px;overflow:hidden;background:radial-gradient(circle at 50% 50%,rgba(40,147,212,.1),transparent 45%),linear-gradient(180deg,#071b2b,#061624);box-shadow:inset 0 0 28px rgba(0,0,0,.24)}.stick-pad:before,.stick-pad:after{content:"";position:absolute;border:1px solid rgba(65,126,170,.12);border-radius:50%;left:18%;right:18%;top:18%;bottom:18%}.stick-pad:after{left:34%;right:34%;top:34%;bottom:34%}.stick-axis{position:absolute;background:rgba(77,157,210,.2)}.stick-axis.horizontal{left:9%;right:9%;top:50%;height:1px}.stick-axis.vertical{top:9%;bottom:9%;left:50%;width:1px}.stick-dot{position:absolute;width:18px;height:18px;border-radius:50%;transform:translate(-50%,-50%);background:#33b9ff;border:3px solid rgba(216,245,255,.85);box-shadow:0 0 18px rgba(49,188,255,.72);transition:left .08s linear,top .08s linear}.stick-top,.stick-bottom{position:absolute;left:8px;color:#7594ac;font-size:7px}.stick-top{top:7px}.stick-bottom{bottom:7px}.virtual-rc-controls{display:grid;gap:7px;padding:0 12px 12px}.virtual-rc-controls label{display:grid;grid-template-columns:34px 1fr 68px;gap:8px;align-items:center;min-height:28px}.virtual-rc-controls label span{color:#7997af;font-size:8px}.virtual-rc-controls label b{color:#b9d8e9;font-size:8px;text-align:right}.virtual-rc-controls input[type=range]{width:100%;accent-color:#2fb4ff}.virtual-rc-controls>button{justify-self:end;min-height:28px;padding:0 10px;border:1px solid rgba(55,166,235,.3);border-radius:5px;background:#0d2c44;color:#a9d7ef;font-size:7px;cursor:pointer}.rc-manual-note{display:flex;gap:8px;align-items:flex-start;margin:0 12px 12px;padding:8px 9px;border:1px solid rgba(77,175,235,.18);border-radius:6px;background:rgba(19,79,116,.1)}.rc-manual-note b{color:#52c8ff;font-size:8px;white-space:nowrap}.rc-manual-note span{color:#7593aa;font-size:7px;line-height:1.5}
.rc-channel-list{display:grid;gap:5px;padding:10px 12px 12px;max-height:330px;overflow:auto}.rc-channel-row{display:grid;grid-template-columns:62px 1fr 62px;gap:8px;align-items:center;min-height:29px}.rc-channel-name{display:grid;grid-template-columns:28px 1fr;align-items:center;gap:4px}.rc-channel-name b{font-size:8px;color:#cce5f5}.rc-channel-name small{font-size:6px;color:#67859e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.rc-channel-bar{position:relative;height:8px;border-radius:999px;background:#071725;border:1px solid rgba(80,132,170,.2);overflow:hidden}.rc-channel-bar i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#176c9f,#31b9ff);box-shadow:0 0 8px rgba(49,185,255,.28)}.rc-channel-bar .center-mark{position:absolute;left:50%;top:-2px;bottom:-2px;width:1px;background:rgba(255,255,255,.32)}.rc-channel-row strong{color:#a8cce1;font-size:8px;text-align:right;font-variant-numeric:tabular-nums}
.rc-config-grid{display:grid;grid-template-columns:minmax(620px,1.4fr) minmax(310px,.8fr);gap:12px}.rc-param-compat-note{display:flex;gap:8px;align-items:flex-start;margin:10px 10px 0;padding:8px 9px;border:1px solid rgba(56,163,229,.2);border-radius:6px;background:rgba(19,86,126,.09)}.rc-param-compat-note b{color:#5dccff;font-size:7px;white-space:nowrap}.rc-param-compat-note span{color:#708ea6;font-size:7px;line-height:1.5}.rc-role-table{padding:10px}.rc-role-head,.rc-role-row{display:grid;grid-template-columns:1.35fr .7fr .72fr .72fr .72fr .72fr .72fr 1fr;gap:6px;align-items:center}.rc-role-head{min-height:26px;padding:0 6px;color:#66859d;font-size:7px;border-bottom:1px solid rgba(79,130,169,.13)}.rc-role-row{min-height:54px;padding:7px 6px;border-bottom:1px solid rgba(76,128,165,.1)}.rc-role-row>div:first-child{display:grid;gap:2px;min-width:0}.rc-role-row>div:first-child b{font-size:8px;color:#d0e7f6}.rc-role-row code{color:#57bfea;font-size:6px;background:transparent}.rc-role-row input,.rc-role-row select{width:100%;min-width:0;height:29px;border:1px solid rgba(87,138,177,.25);border-radius:5px;background:#071a2a;color:#c7e0ef;padding:0 6px;font-size:7px;outline:none}.rc-role-row input:focus,.rc-role-row select:focus{border-color:#2eaff9}.rc-normalized{position:relative;height:29px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(79,135,176,.2);border-radius:5px;background:#061725;overflow:hidden}.rc-normalized i{position:absolute;left:0;top:0;bottom:0;background:rgba(35,166,236,.17);border-right:1px solid rgba(58,194,255,.45)}.rc-normalized b{position:relative;z-index:1;color:#acd8ed;font-size:7px}
.rc-check-pill{padding:4px 8px;border-radius:999px;font-size:7px;font-weight:700}.rc-check-pill.ok{color:#5ce19a;border:1px solid rgba(66,218,132,.28);background:rgba(35,121,75,.13)}.rc-check-pill.warn{color:#f0bd57;border:1px solid rgba(240,189,87,.28);background:rgba(124,91,31,.12)}.rc-capture-panel{display:grid;gap:9px;padding:11px 12px;border-bottom:1px solid rgba(83,137,177,.13)}.capture-copy{display:grid;gap:3px}.capture-copy b{color:#d1e8f6;font-size:9px}.capture-copy small{color:#6f8da5;font-size:7px;line-height:1.5}.capture-actions{display:flex;gap:6px}.capture-actions button,.rc-actions button,.link-safety-button{min-height:29px;border:1px solid rgba(62,157,219,.28);border-radius:5px;background:#0b2a42;color:#a9d6ef;padding:0 9px;font-size:7px;cursor:pointer}.capture-actions button:hover:not(:disabled),.rc-actions button:hover:not(:disabled),.link-safety-button:hover{border-color:#2eb2fb;background:#104b70;color:#fff}.capture-actions button:disabled,.rc-actions button:disabled{opacity:.36;cursor:not-allowed}.capture-actions .capture-stop{border-color:rgba(242,179,70,.32);background:rgba(118,83,22,.2);color:#e8c16f}.capture-ranges{display:grid;grid-template-columns:1fr 1fr;gap:6px}.capture-ranges>div{display:flex;justify-content:space-between;gap:8px;padding:7px 8px;border:1px solid rgba(81,132,169,.14);border-radius:5px;background:rgba(6,23,37,.52)}.capture-ranges span{color:#6f8ca4;font-size:7px}.capture-ranges b{color:#b9d5e7;font-size:7px}.rc-issue-list{display:grid;gap:6px;padding:10px 12px}.rc-no-issues,.rc-issue{display:flex;gap:8px;align-items:center;min-height:43px;padding:7px 8px;border-radius:6px}.rc-no-issues{border:1px solid rgba(66,213,130,.2);background:rgba(32,117,71,.1)}.rc-no-issues>span,.rc-issue>span{width:22px;height:22px;display:grid;place-items:center;border-radius:50%;font-weight:900}.rc-no-issues>span{background:#34b46e;color:#fff}.rc-no-issues>div,.rc-issue>div{display:grid;gap:2px}.rc-no-issues b{color:#65df9a;font-size:8px}.rc-no-issues small,.rc-issue small{color:#708ca3;font-size:7px;line-height:1.45}.rc-issue{border:1px solid rgba(239,184,73,.24);background:rgba(122,89,27,.1)}.rc-issue.error{border-color:rgba(255,88,78,.3);background:rgba(124,35,31,.13)}.rc-issue>span{background:#bd8f35;color:white}.rc-issue.error>span{background:#d04b44}.rc-issue b{color:#eac574;font-size:8px}.rc-issue.error b{color:#ff9189}.rc-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:0 12px 11px}.rc-actions .primary-action{border-color:#2facf3;background:#0d6c9e;color:#fff}.rc-actions .verify-action{border-color:rgba(78,213,140,.3);background:rgba(28,108,66,.22);color:#80e4ab}.rc-message{margin:0 12px 12px;padding:8px 9px;border-radius:6px;font-size:7px;line-height:1.5}.rc-message.info{border:1px solid rgba(65,156,216,.24);background:rgba(24,89,129,.11);color:#88c7ec}.rc-message.success{border:1px solid rgba(67,212,132,.24);background:rgba(31,119,72,.11);color:#72dfa0}.rc-message.warn{border:1px solid rgba(239,184,77,.26);background:rgba(122,88,29,.11);color:#e9c675}.rc-message.error{border:1px solid rgba(255,91,81,.28);background:rgba(124,35,31,.14);color:#ff9992}
.rc-failsafe-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding:11px 12px 12px}.rc-failsafe-grid>div{min-height:62px;display:grid;align-content:center;gap:3px;padding:8px 10px;border:1px solid rgba(81,135,176,.14);border-radius:7px;background:rgba(6,24,39,.56)}.rc-failsafe-grid span{color:#6d8aa2;font-size:7px}.rc-failsafe-grid b{color:#d1e8f6;font-size:10px}.rc-failsafe-grid code{color:#50bfe9;font-size:6px}.rc-failsafe-grid small{color:#6d879c;font-size:6px;line-height:1.4}.link-safety-button{min-height:25px}.ok-text{color:#5bdc94!important}.warn-text{color:#efbd59!important}

.module-placeholder { min-height:550px;display:flex;align-items:center;justify-content:center;gap:28px;padding:50px; }
.module-icon { width:84px;height:84px;display:grid;place-items:center;border-radius:24px;border:1px solid rgba(44,171,255,.28);background:rgba(21,103,158,.12);color:#5fcaff;font-size:38px; }
.module-placeholder h2 { margin:0 0 12px;font-size:24px; }.module-placeholder p { max-width:660px;color:#809bb5;line-height:1.7;font-size:12px; }
.placeholder-actions { display:flex;gap:10px;margin-top:18px; }.placeholder-actions button { border:1px solid var(--line);background:#0c263c;color:#a9c9e1;border-radius:6px;padding:9px 14px;cursor:pointer; }.placeholder-actions .primary-action { border-color:#279ddd;background:#126da6;color:white; }
.debug-rightbar { display:flex;flex-direction:column;gap:10px; }
.status-grid { display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:10px; }
.status-grid > div { display:flex;justify-content:space-between;align-items:center;min-height:36px;padding:0 9px;border:1px solid rgba(86,137,177,.14);border-radius:6px;background:rgba(7,25,40,.62);font-size:9px; }
.status-grid span { color:#7995ad; }.status-grid b { color:#dbeeff;font-size:10px; }.status-grid .ok { color:#54e492; }.status-grid .bad { color:#ff746e; }.status-grid .warn { color:#efba51; }.status-grid .standby { color:#f1c457;background:rgba(133,97,23,.22);padding:2px 5px;border-radius:4px; }
.prearm-alert { margin:0 10px 10px;display:flex;gap:10px;align-items:center;padding:9px;border:1px solid rgba(255,83,74,.48);border-radius:6px;background:rgba(128,31,29,.22); }
.prearm-alert > span { width:23px;height:23px;display:grid;place-items:center;border-radius:50%;background:#ef4b43;color:white;font-weight:900; }.prearm-alert div { display:grid;gap:2px; }.prearm-alert b { color:#ff766e;font-size:10px; }.prearm-alert small { color:#a87976;font-size:8px; }
.prearm-alert.passed { border-color:rgba(69,218,135,.32);background:rgba(34,121,74,.14); }.prearm-alert.passed > span { background:#35b86f; }.prearm-alert.passed b { color:#65e59b; }.prearm-alert.passed small { color:#79a990; }
.bridge-surface { padding:5px 10px; }
.bridge-error { margin:7px 0 4px;padding:7px 8px;border:1px solid rgba(255,102,91,.3);border-radius:6px;background:rgba(119,38,34,.18);color:#ff9c95;font-size:8px;line-height:1.45; }
.bridge-controls { display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:7px 0 8px;border-top:1px solid rgba(89,138,178,.12); }
.bridge-controls button,.param-actions button { min-height:30px;border:1px solid rgba(66,158,219,.32);border-radius:5px;background:#0e2b43;color:#a9d7f3;font-size:8px;cursor:pointer; }
.bridge-controls button:hover:not(:disabled),.param-actions button:hover:not(:disabled){border-color:#2aaeff;background:#124a70;color:white}.bridge-controls button:disabled,.param-actions button:disabled{opacity:.38;cursor:not-allowed}
.param-tool { padding:8px 0;border-top:1px solid rgba(89,138,178,.12); }
.param-row { display:grid;grid-template-columns:1.45fr .7fr;gap:6px; }
.param-row input { min-width:0;height:31px;border:1px solid rgba(91,141,180,.24);border-radius:5px;background:#071a2a;color:#d6eaff;padding:0 8px;font-size:8px;outline:none; }
.param-row input:focus { border-color:#2caef7;box-shadow:0 0 0 2px rgba(44,174,247,.08); }
.param-actions { display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px; }
.param-tool > small { display:block;margin-top:6px;color:#86a8c4;font-size:7px;line-height:1.4;word-break:break-all; }
.bridge-row.secondary { opacity:.65; }

.bridge-row { display:grid;grid-template-columns:12px 1fr auto;align-items:center;gap:8px;padding:8px 2px; }.bridge-row + .bridge-row { border-top:1px solid rgba(89,138,178,.12); }.bridge-row .dot { width:7px;height:7px;border-radius:50%; }.dot.online { background:#43df84;box-shadow:0 0 10px #43df84; }.dot.demo { background:#e6b64d;box-shadow:0 0 8px rgba(230,182,77,.4); }.bridge-row div { display:grid;gap:1px; }.bridge-row b { font-size:9px; }.bridge-row small { color:#6e8da9;font-size:7px; }.bridge-row strong { color:#87a4bc;font-size:8px; }
.log-surface { flex:1;min-height:270px; }.clear-log { border:0;background:transparent;color:#6686a1;font-size:7px;cursor:pointer; }
.timeline { padding:8px 10px 12px;max-height:330px;overflow:auto; }.log-item { position:relative;display:grid;grid-template-columns:58px 1fr;gap:7px;padding:7px 3px 7px 18px;border-left:1px solid rgba(57,132,185,.34);margin-left:4px; }.timeline-dot { position:absolute;left:-4px;top:14px;width:7px;height:7px;border-radius:50%;background:#268ddd;box-shadow:0 0 8px rgba(38,141,221,.5); }.log-item.error .timeline-dot { background:#ff4f48; }.log-item.success .timeline-dot { background:#46d985; }.log-item.warn .timeline-dot { background:#ecb84f; }.log-item time { color:#809cb4;font-size:8px; }.log-item div { display:grid;gap:2px; }.log-item b { font-size:9px; }.log-item small { color:#6e8ba4;font-size:7px;line-height:1.4; }.empty-log { color:#597892;text-align:center;padding:30px 0;font-size:9px; }
.score-surface { display:grid;grid-template-columns:40px 112px 1fr;align-items:center;padding:12px; }.trophy { color:#f3c443;font-size:27px; }.score-surface > div { display:grid; }.score-surface small { color:#8aa4bb;font-size:8px; }.score-surface b { font-size:28px;color:#ffd163;line-height:1; }.score-surface b em { font-size:12px;color:#92aabe;font-style:normal;margin-left:3px; }.remaining { padding-left:12px;border-left:1px solid rgba(94,141,178,.18); }.remaining span { color:#7894ad;font-size:8px; }.remaining b { color:#94aec4;font-size:9px;line-height:1.4;margin-top:3px; }
.right-actions { display:grid;grid-template-columns:1fr 1fr;gap:8px; }.right-actions button,.flight-action { min-height:42px;display:grid;place-items:center;border-radius:6px;text-decoration:none;cursor:pointer;font-size:9px; }.right-actions button { border:1px solid rgba(110,155,193,.5);background:#10263a;color:#b7d2e8; }.flight-action { border:1px solid #2baeff;background:linear-gradient(180deg,#159eea,#0871b8);color:white;box-shadow:0 0 18px rgba(35,164,241,.17); }
@media(max-width:1450px){ .safety-field{grid-template-columns:minmax(0,1fr) 145px}.safety-diagnostic-body{grid-template-columns:1fr 185px}.sensor-hero-grid{grid-template-columns:1fr}.attitude-panel{grid-template-columns:210px 1fr}.calibration-card{grid-template-columns:minmax(0,1fr) 100px 82px}.sensor-card-grid{grid-template-columns:1fr 1fr}  .debug-page{grid-template-columns:220px minmax(620px,1fr) 350px}.scene-and-controls{grid-template-columns:minmax(0,1fr) 108px}.metric-grid{gap:7px;padding:9px}.debug-rightbar{padding:12px 9px}.debug-sidebar{padding-left:9px;padding-right:9px} }
@media(max-width:1180px){ .safety-card-grid{grid-template-columns:1fr}.safety-summary-strip{grid-template-columns:1fr 1fr}.debug-page{grid-template-columns:190px minmax(590px,1fr)}.debug-rightbar{display:none}.power-layout{grid-template-columns:1fr}.parameter-surface{display:none}.lower-grid{grid-template-columns:1fr}.debug-sidebar{font-size:90%} }


/* Pre-flight gate */
.preflight-workbench{display:grid;gap:14px;min-height:0}.preflight-hero{display:flex;align-items:center;justify-content:space-between;padding:24px 26px;border-color:rgba(96,165,250,.28);background:linear-gradient(135deg,rgba(9,32,51,.96),rgba(7,22,36,.96))}.preflight-hero.ready{box-shadow:inset 4px 0 #48df8b}.preflight-hero.blocked{box-shadow:inset 4px 0 #ff6b62}.preflight-kicker{font-size:10px;letter-spacing:.18em;color:#55d9ff}.preflight-hero h2{margin:6px 0 8px;font-size:24px;color:#eef8ff}.preflight-hero p{max-width:760px;margin:0;color:#7897b5;line-height:1.65}.preflight-permit{display:flex;align-items:center;gap:12px;min-width:320px;justify-content:flex-end}.permit-ring{display:grid;place-items:center;width:54px;height:54px;border-radius:50%;font-size:25px;font-weight:800;border:1px solid}.permit-ring.pass{color:#48df8b;background:rgba(72,223,139,.09);border-color:rgba(72,223,139,.5)}.permit-ring.block{color:#ff6b62;background:rgba(255,94,87,.08);border-color:rgba(255,94,87,.45)}.preflight-permit small,.preflight-final-copy small{display:block;color:#7897b5}.preflight-permit b{display:block;margin-top:4px;color:#e9f5ff}.preflight-permit strong{font-size:29px;color:#55d9ff}.preflight-permit strong em{font-size:12px;color:#7897b5;font-style:normal}.preflight-check-surface,.preflight-aircraft-summary,.preflight-blocker-surface,.preflight-final-surface{padding:16px}.preflight-count-pill{padding:5px 10px;border-radius:999px;font-size:11px}.preflight-count-pill.ok{color:#48df8b;background:rgba(72,223,139,.09)}.preflight-count-pill.warn{color:#f0bd45;background:rgba(240,189,69,.09)}.preflight-check-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.preflight-check-card{display:grid;grid-template-columns:38px 1fr auto;gap:11px;align-items:center;padding:14px;border:1px solid var(--line);border-radius:10px;background:rgba(5,18,30,.54)}.preflight-check-card.pass{border-color:rgba(72,223,139,.25)}.preflight-check-card.block{border-color:rgba(255,94,87,.3)}.preflight-check-card.warn{border-color:rgba(240,189,69,.3)}.check-state-icon{display:grid;place-items:center;width:34px;height:34px;border-radius:8px;background:rgba(120,151,181,.1);font-weight:800}.pass .check-state-icon{color:#48df8b}.block .check-state-icon{color:#ff6b62}.warn .check-state-icon{color:#f0bd45}.check-copy span{font-size:10px;color:#7897b5}.check-copy b{display:block;margin:3px 0;color:#e1effb}.check-copy small{display:block;color:#6f8aa4;line-height:1.45}.preflight-check-card button{padding:6px 10px;border:1px solid rgba(85,217,255,.24);border-radius:7px;background:rgba(40,168,255,.08);color:#73dfff}.preflight-lower-grid{display:grid;grid-template-columns:1fr 1.35fr;gap:14px}.preflight-aircraft-summary dl{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0}.preflight-aircraft-summary dl div{padding:10px;border-radius:8px;background:rgba(6,22,36,.62)}.preflight-aircraft-summary dt{font-size:10px;color:#7897b5}.preflight-aircraft-summary dd{margin:4px 0 0;color:#dceaf6;font-weight:700}.preflight-clear,.preflight-issue{display:flex;gap:10px;padding:11px;border-radius:8px;margin-bottom:8px}.preflight-clear{background:rgba(72,223,139,.07);color:#48df8b}.preflight-issue.block{background:rgba(255,94,87,.07);color:#ff8b84}.preflight-issue.warn{background:rgba(240,189,69,.07);color:#f0bd45}.preflight-clear small,.preflight-issue small{display:block;margin-top:3px;color:#7897b5}.preflight-final-surface{display:flex;align-items:center;justify-content:space-between;gap:16px}.preflight-final-copy b{color:#e9f5ff}.preflight-final-actions{display:flex;gap:9px}.preflight-final-actions button,.preflight-flight-button{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:0 16px;border-radius:8px;border:1px solid rgba(85,217,255,.28);background:rgba(40,168,255,.1);color:#bfeaff;text-decoration:none}.preflight-flight-button{background:#168ee0;color:white;border-color:#28a8ff}.preflight-flight-button.disabled,.right-actions .flight-action.disabled{opacity:.45;cursor:not-allowed}.right-actions button.flight-action{font:inherit}



/* Fault Training V1 */
.training-sidebar-section{position:relative}.training-side-title{display:flex;align-items:center;justify-content:space-between}.training-side-title small{color:#50c9f3;font-size:7px}.training-current-card{border-color:rgba(85,217,255,.42)!important;background:linear-gradient(135deg,rgba(23,115,168,.23),rgba(8,39,62,.75))!important}.training-current-card small{color:#7ddcff!important}.training-library-button{width:100%;display:grid;grid-template-columns:24px 1fr 12px;align-items:center;gap:7px;margin-top:7px;padding:9px 8px;border:1px dashed rgba(85,217,255,.28);border-radius:7px;background:rgba(16,66,98,.22);color:#bdeaff;text-align:left;cursor:pointer}.training-library-button>span{display:grid;place-items:center;width:22px;height:22px;border-radius:6px;background:rgba(40,168,255,.12);color:#55d9ff}.training-library-button div{display:grid;gap:1px}.training-library-button b{font-size:9px}.training-library-button small{color:#678da9;font-size:7px}.training-library-button strong{color:#55d9ff;font-size:16px}.training-library-button:hover{border-color:rgba(85,217,255,.55);background:rgba(20,91,132,.28)}.training-catalog-error{display:block;margin-top:6px;color:#ff9089;font-size:7px;line-height:1.4}
.training-task-hud{display:grid;grid-template-columns:minmax(250px,1.35fr) minmax(330px,1fr) auto;gap:12px;align-items:center;margin-bottom:12px;padding:11px 13px;border:1px solid rgba(85,217,255,.25);border-radius:9px;background:linear-gradient(135deg,rgba(9,38,58,.96),rgba(8,26,42,.96));box-shadow:inset 3px 0 #25aef0}.training-task-main{display:flex;align-items:center;gap:10px;min-width:0}.training-case-code{flex:0 0 auto;padding:4px 7px;border-radius:6px;background:rgba(85,217,255,.1);color:#64dfff;font-size:8px;font-weight:800;letter-spacing:.05em}.training-task-main div{min-width:0;display:grid;gap:3px}.training-task-main b{color:#ecf8ff;font-size:11px}.training-task-main small{overflow:hidden;color:#7b9ab5;font-size:8px;line-height:1.4;text-overflow:ellipsis;white-space:nowrap}.training-task-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.training-task-meta>div{display:grid;gap:2px;padding:7px 8px;border:1px solid rgba(92,142,181,.14);border-radius:6px;background:rgba(5,19,31,.55)}.training-task-meta span{color:#668aa7;font-size:6px}.training-task-meta b{overflow:hidden;color:#cfe8f8;font-size:8px;text-overflow:ellipsis;white-space:nowrap}.training-task-actions{display:grid;grid-template-columns:repeat(2,90px);gap:5px}.training-task-actions button{min-height:29px;border:1px solid rgba(87,154,202,.26);border-radius:6px;background:#0d2b42;color:#a9d3eb;font-size:7px;cursor:pointer}.training-task-actions button:hover{border-color:#2aaeff;color:white}.training-task-actions .training-submit{border-color:#249fdc;background:#116da3;color:#fff}.training-task-actions .training-exit{color:#93a8b9}.training-hint,.training-result{grid-column:1/-1;display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:6px}.training-hint{border:1px solid rgba(240,189,69,.25);background:rgba(111,80,25,.12);color:#d8b86d}.training-hint b{font-size:8px}.training-hint span{font-size:8px;line-height:1.45}.training-result{display:grid;grid-template-columns:1fr auto minmax(260px,1fr);border:1px solid rgba(255,112,99,.22);background:rgba(105,37,32,.1)}.training-result.passed{border-color:rgba(72,223,139,.24);background:rgba(34,113,72,.1)}.training-result div{display:grid;gap:2px}.training-result b{color:#f2f8fc;font-size:9px}.training-result small,.training-result>span{color:#7f9ab1;font-size:7px}.training-result strong{font-size:20px;color:#f3c85e}.training-result.passed strong{color:#58df91}.training-result strong em{font-size:9px;font-style:normal;color:#839caf}
.training-library-backdrop{position:fixed;z-index:1000;inset:58px 0 0;display:grid;place-items:center;padding:26px;background:rgba(2,9,16,.72);backdrop-filter:blur(6px)}.training-library-panel{width:min(1180px,94vw);max-height:86vh;overflow:auto;border:1px solid rgba(85,217,255,.25);border-radius:14px;background:linear-gradient(180deg,#0a1b2b,#071420);box-shadow:0 28px 80px rgba(0,0,0,.42);color:#dcecf8}.training-library-panel>header{display:flex;justify-content:space-between;gap:20px;padding:22px 24px 16px;border-bottom:1px solid rgba(88,137,176,.15)}.training-library-panel header>div>span{color:#53d8ff;font-size:8px;font-weight:800;letter-spacing:.16em}.training-library-panel h2{margin:5px 0 6px;font-size:22px}.training-library-panel p{margin:0;color:#7694ad;font-size:10px}.training-close{width:34px;height:34px;border:1px solid rgba(113,155,190,.2);border-radius:8px;background:rgba(255,255,255,.04);color:#a8c2d6;font-size:22px;cursor:pointer}.training-filter-row{display:flex;gap:7px;padding:14px 24px}.training-filter-row button{padding:6px 12px;border:1px solid rgba(89,139,180,.2);border-radius:999px;background:rgba(8,29,47,.65);color:#7898b2;font-size:8px;cursor:pointer}.training-filter-row button.active{border-color:rgba(85,217,255,.45);background:rgba(29,126,179,.18);color:#82e4ff}.training-case-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:0 24px 24px}.training-case-card{display:grid;gap:11px;padding:15px;border:1px solid rgba(91,143,183,.18);border-radius:10px;background:rgba(7,24,39,.8);box-shadow:0 8px 22px rgba(0,0,0,.12)}.training-case-card:hover{border-color:rgba(85,217,255,.32);transform:translateY(-1px)}.training-case-card-head{display:grid;grid-template-columns:34px 1fr auto;gap:9px;align-items:center}.training-case-icon{display:grid;place-items:center;width:34px;height:34px;border-radius:8px;background:rgba(40,168,255,.11);color:#61dcff;font-size:17px}.training-case-card-head div{display:grid;gap:2px}.training-case-card-head small{color:#6586a2;font-size:7px}.training-case-card-head b{color:#e6f3fb;font-size:11px}.training-case-card-head strong{color:#efc45a;font-size:10px;letter-spacing:1px}.training-case-card>p{min-height:35px;margin:0;color:#8aa5bb;font-size:9px;line-height:1.55}.training-case-card dl{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:0}.training-case-card dl div{padding:7px 8px;border-radius:6px;background:rgba(4,17,29,.7)}.training-case-card dt{color:#63839d;font-size:6px}.training-case-card dd{margin:3px 0 0;color:#bbd3e4;font-size:8px}.training-case-task{display:grid;gap:3px;padding:8px 9px;border-left:2px solid rgba(85,217,255,.36);background:rgba(20,75,108,.12)}.training-case-task b{color:#65dcff;font-size:7px}.training-case-task span{color:#839eb4;font-size:8px;line-height:1.5}.training-start-button{min-height:34px;border:1px solid #249fdc;border-radius:7px;background:linear-gradient(180deg,#168fd0,#0e6d9f);color:white;font-size:9px;font-weight:700;cursor:pointer}.training-start-button:hover{filter:brightness(1.08)}
@media(max-width:1400px){.training-task-hud{grid-template-columns:1fr 1fr}.training-task-actions{grid-column:1/-1;grid-template-columns:repeat(4,1fr)}.training-case-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:980px){.training-case-grid{grid-template-columns:1fr}.training-task-meta{grid-template-columns:1fr 1fr}}

</style>
