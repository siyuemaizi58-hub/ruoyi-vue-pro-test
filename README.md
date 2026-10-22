# RuoYi-Vue-Pro（芋道 yudao）管理后台 API 测试

对国内主流企业级 Java 全栈框架 **RuoYi-Vue-Pro（yudao）** 的管理后台 REST API 进行的一次接口/功能测试实践。

## 测试范围

| 模块 | 覆盖内容 |
| --- | --- |
| 登录鉴权 | 账号密码登录、错误密码、不存在账号、字段边界值、token 鉴权 |
| 用户管理 | 分页查询、创建、重复校验、字段校验、更新/删除 |
| 角色管理 | 分页、创建、重复编码、必填校验 |
| 部门/字典 | 部门列表、字典类型/数据分页 |
| 权限控制 | 登出、旧 token 失效、多租户数据隔离 |
| 边界与异常 | 分页边界、邮箱/手机号格式、账号格式一致性 |

用例设计方法：**等价类划分 + 边界值分析 + 异常场景 + 越权/一致性校验**。

## 测试结果

```
汇总：41 通过 / 43 用例，2 个缺陷（详见《缺陷清单.md》）
```

| 指标 | 数值 |
| --- | --- |
| 用例总数 | 43 |
| 通过 | 41 |
| 缺陷 | 2 |

## 运行环境

- 后端：SpringBoot 2.7 + MyBatis Plus + Druid（yudao-server，端口 48080）
- 数据库：MySQL 8.0.36（ruoyi-vue-pro-jdk8）
- 缓存：Redis 5.0.14
- JDK：17.0.20.1（Temurin）
- 脚本：Python 3.12 + httpx

## 如何运行

1. 启动 yudao-server 后端（`java -jar yudao-server.jar --spring.profiles.active=local`），确保 MySQL / Redis 已就绪。
2. 安装依赖：`pip install httpx`
3. 运行测试：`python tests/test_ruoyi_admin_api.py`

## 文档

- [测试报告](测试报告.md)
- [缺陷清单](缺陷清单.md)
- [测试脚本](tests/test_ruoyi_admin_api.py)
