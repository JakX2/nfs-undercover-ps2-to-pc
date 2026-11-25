# V803: avoid historical reply-route CI collisions

V79 and V80 used unbounded version-prefix patterns that also triggered on V790–V799 and V800–V809 changes. Recent callback development consequently queued unrelated historical owner runs. Narrow both filters to explicit version separators; preserve workflow_dispatch, existing concurrency policy, branch and workflow-file triggers, and all existing validation steps. This change does not disable either original test or cancel current jobs. The new V802 original callback/time fixture remains independently triggered.
