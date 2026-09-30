# 已知问题

本文件只记录经过自动化测试重新验证的问题。测试失败不等于产品一定有缺陷，必须先排除环境和测试脚本问题。

## BUG-001：刷新历史会话时短暂显示新聊天欢迎页

- 对应测试：`test_refresh_does_not_flash_new_chat_hero`
- 当前状态：在本次被测版本中未复现，回归测试正常通过
- 预期：刷新已有历史的会话时，始终显示加载状态或历史消息。
- 实际：人为延迟 `/api/sessions` 1.5 秒后刷新，历史消息正常出现，检测器没有观察到欢迎页。
- 验证环境：Windows 10、Python 3.12、Chromium、nanobot commit `7cede64f`。

## BUG-002：附件不能通过拖拽调整顺序

- 对应测试：`test_attachments_can_be_reordered_by_dragging`
- 当前状态：已确认，测试使用严格 `xfail` 跟踪
- 预期：把第一个附件拖到最后一个附件的位置后，附件顺序发生变化。
- 实际：上传顺序为 `a.txt`、`b.txt`、`c.txt`，拖动 `a.txt` 后最后一个仍为 `c.txt`。
- 验证环境：Windows 10、Python 3.12、Chromium、nanobot commit `7cede64f`。
- 复现命令：`python -m pytest tests/ui/test_known_bugs.py::test_attachments_can_be_reordered_by_dragging --runxfail`。
- 证据位置：用上面的命令复现失败后，查看 `test-results/` 中的截图和 trace。
