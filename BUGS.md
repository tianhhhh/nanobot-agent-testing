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
- 复现命令：`python -m pytest tests/ui/test_attachments.py::test_attachments_can_be_reordered_by_dragging --runxfail`。
- 证据位置：用上面的命令复现失败后，查看 `test-results/` 中的截图和 trace。

## BUG-003：损坏的 Base64 图片被静默忽略

- 对应测试：`test_corrupted_base64_image_is_rejected_without_saving`
- 当前状态：自动化已复现，使用严格 `xfail` 跟踪。
- 预期：返回 `400 invalid_request_error`，并说明 Base64 数据无效。
- 实际：解码函数返回空结果，接口继续执行普通对话并返回成功。
- 风险：调用方无法区分“图片分析成功”和“图片没有被服务端接收”。
- 复现命令：`python -m pytest tests/api/test_chat_attachments.py -k corrupted --runxfail`。

## BUG-004：SSE 上游中途异常后仍返回正常完成标记

- 对应测试：`test_interrupted_sse_does_not_emit_normal_done_marker`
- 当前状态：自动化已复现，使用严格 `xfail` 跟踪。
- 预期：模型流没有完成原因或中途断开时，API 不得返回 `data: [DONE]`。
- 实际：上游只产生部分数据后断流，客户端仍收到 `finish_reason=stop` 和 `[DONE]`。
- 风险：调用方会把不完整回答误判为正常完成，无法触发重试或错误提示。
- 复现命令：`python -m pytest tests/api/test_chat_resilience.py -k interrupted --runxfail`。

## BUG-005：停止响应未可靠取消后台生成

- 对应测试：`test_stop_response_terminates_slow_stream_and_allows_next_turn`
- 当前状态：自动化已复现，测试使用严格 `xfail` 跟踪。
- 预期：点击“停止响应”后终止当前生成，下一轮普通对话能够及时执行。
- 实际：慢速请求仍在后台运行约 22 秒；按钮可能持续显示，或下一轮请求等待旧请求自然结束。
- 风险：用户认为任务已经停止，但模型调用仍占用资源，并阻塞后续交互。
- 复现命令：`python -m pytest tests/ui/test_chat_resilience.py -k stop_response --runxfail`。
- 证据位置：Gateway 日志中停止操作后，原慢速请求仍然输出完整 `Response`。

## 已排除：错误 Content-Type 的 JSON 请求

- 原测试：`test_chat_rejects_json_sent_with_an_unsupported_content_type`
- 排查结论：不是已确认的产品缺陷。当前接口约定支持 JSON 和 multipart，但没有规定
  `text/plain` 必须返回 `400` 或 `415`；服务端对非 multipart 请求尝试解析 JSON 属于宽松兼容行为。
- 处理：移除错误的 `xfail`，替换为对 `application/json; charset=utf-8` 的合法兼容性验证。
