# qiscord

基于[go-cqhttp](https://docs.go-cqhttp.org/)的应答bot。

## 使用方法

1. 启动go-cqhttp，在config.yml中设置servers：

```yml
# 纯示例，可根据实际情况修改
servers:
  - http:
      host: 127.0.0.1
      port: 5700
      timeout: 5
      long-polling:
        enabled: false
        max-queue-size: 2000
      middlewares:
        <<: *default
      post:
        - url: "http://127.0.0.1:19198"
          secret: ''
```

1. 启动``main.py``，或者在代码中直接引用：

```python
    listener = qiscord.listener.Listenter(print_info=True)
    listener.start()
```