import DataSourceHealth from "../components/DataSourceHealth";

// Settings page — hosts Data Source Health (moved off Dashboard per commit 2 of the Phase 1
// migration; see /Users/cullen/.claude/plans/vivid-wibbling-cake.md). No dedicated system-config
// code existed in the legacy app beyond this, so that's all this page has for now.
export default function Settings() {
  return (
    <div>
      <div className="page-head">
        <div>
          <div className="page-title">Settings</div>
          <div className="muted">系统配置与数据源状态。</div>
        </div>
      </div>
      <DataSourceHealth />
    </div>
  );
}
