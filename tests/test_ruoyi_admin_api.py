# -*- coding: utf-8 -*-
"""
若依 RuoYi-Vue-Pro（芋道 yudao）管理后台 API 测试脚本
====================================================
被测对象：yudao-server 后端（SpringBoot 2.7 + MySQL 8.0 + Redis）
接口根路径：http://127.0.0.1:48080/admin-api
鉴权方式：Header Authorization: Bearer <accessToken>，Header tenant-id: 1
响应约定：HTTP 恒为 200，业务结果在 body.code（0=成功，400=参数错误，401=未登录，
          403=无权限，1002xxxxxx=业务错误码）

覆盖范围：登录鉴权 / 用户管理 / 角色管理 / 部门 / 字典 / 权限控制 / 边界与异常
方法：等价类划分 + 边界值分析 + 异常场景 + 越权与一致性校验

运行前提：后端已启动 http://127.0.0.1:48080
运行：    python test_ruoyi_admin_api.py
"""
import sys
import io
import uuid
import httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "http://127.0.0.1:48080"
client = httpx.Client(timeout=30, trust_env=False)

TOKEN = None
PASS = FAIL = 0
CASES = []  # (编号, 名称, 期望, 实际code, 结论, 备注)


def _post(path, json=None, params=None, auth=True, tenant="1"):
    headers = {"tenant-id": tenant}
    if auth and TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    r = client.post(BASE + path, json=json, params=params, headers=headers)
    try:
        return r.json()
    except Exception:
        return {}


def _get(path, params=None, auth=True, tenant="1"):
    headers = {"tenant-id": tenant}
    if auth and TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    r = client.get(BASE + path, params=params, headers=headers)
    try:
        return r.json()
    except Exception:
        return {}


def _put(path, json=None, auth=True):
    headers = {"tenant-id": "1"}
    if auth and TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    r = client.put(BASE + path, json=json, headers=headers)
    try:
        return r.json()
    except Exception:
        return {}


def _delete(path, params=None, auth=True):
    headers = {"tenant-id": "1"}
    if auth and TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    r = client.request("DELETE", BASE + path, params=params, headers=headers)
    try:
        return r.json()
    except Exception:
        return {}


def rec(no, name, body, expected, note=""):
    """expected: int 表示期望 code；'ok' 表示期望成功(0)；'err' 表示期望任何非 0 错误码。"""
    global PASS, FAIL
    code = body.get("code")
    if expected == "ok":
        ok = (code == 0)
    elif expected == "err":
        ok = (code not in (0, None))
    else:
        ok = (code == expected)
    mark = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    msg = body.get("msg", "")
    CASES.append((no, name, expected, code, ok, msg))
    print(f"  [{mark}] {no} {name} | 期望={expected} 实际code={code} {msg[:50]}")


def uniq(prefix):
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def login(username, password):
    global TOKEN
    body = _post("/admin-api/system/auth/login",
                 json={"username": username, "password": password}, auth=False)
    if body.get("code") == 0:
        TOKEN = body["data"]["accessToken"]
    return body


print("=" * 72)
print("步骤 0：管理员登录")
print("=" * 72)
body = login("admin", "admin123")
rec("S0", "admin/admin123 登录成功", body, "ok")
if body.get("code") != 0:
    print("!! 登录失败，请确认后端已启动、数据库已导入。响应：", body)
    sys.exit(1)
print(f"   登录成功，token={TOKEN[:16]}...")


print()
print("=" * 72)
print("用例组 A — 登录鉴权（等价类 / 边界值 / 异常）")
print("=" * 72)

rec("A1", "正确密码登录成功", login("admin", "admin123"), "ok")
rec("A2", "错误密码登录被拒", login("admin", "wrongpass"), "err")
rec("A3", "不存在账号登录被拒", login(uniq("noexist"), "admin123"), "err")
rec("A4", "空用户名被拒(400)", login("", "admin123"), 400)
rec("A5", "空密码被拒(400)", login("admin", ""), 400)
rec("A6", "用户名3位(<4)被拒(400)", login("abc", "admin123"), 400)
rec("A7", "用户名31位(>30)被拒(400)", login("a" * 31, "admin123"), 400)
rec("A8", "用户名含下划线被拒(400)", login("admin_", "admin123"), 400)
rec("A9", "密码17位(>16)被拒(400)", login("admin", "p" * 17), 400)

body = _get("/admin-api/system/user/page", params={"pageNo": 1, "pageSize": 10}, auth=False)
rec("A10", "未携带token访问被拒(401)", body, 401)


print()
print("=" * 72)
print("用例组 B — 用户管理（CRUD + 边界 + 重复校验）")
print("=" * 72)

body = _get("/admin-api/system/user/page", params={"pageNo": 1, "pageSize": 10})
rec("B1", "用户分页查询成功", body, "ok")

body = _get("/admin-api/system/user/get", params={"id": 1})
rec("B2", "查询存在的用户返回数据", body, "ok")

u = uniq("tester")
body = _post("/admin-api/system/user/create", json={
    "username": u, "nickname": "测试用户", "password": "test1234",
    "deptId": 103, "email": f"{u}@test.com",
    "mobile": "13800138000", "sex": 1, "status": 0})
rec("B3", "创建合法用户成功", body, "ok")
new_user_id = body.get("data")

body = _post("/admin-api/system/user/create", json={
    "username": u, "nickname": "重复", "password": "test1234"})
rec("B4", "重复用户名被拒(业务码)", body, "err")

body = _post("/admin-api/system/user/create", json={
    "username": "ab", "nickname": "短", "password": "test1234"})
rec("B5", "用户名过短(<4)被拒(400)", body, 400)

body = _post("/admin-api/system/user/create", json={
    "username": uniq("pw"), "nickname": "短密码", "password": "123"})
rec("B6", "密码过短(<4)被拒(400)", body, 400)

body = _post("/admin-api/system/user/create", json={
    "username": uniq("mail"), "nickname": "邮箱", "password": "test1234",
    "email": "not-an-email"})
rec("B7", "非法邮箱被拒(400)", body, 400)

body = _post("/admin-api/system/user/create", json={
    "username": uniq("mob"), "nickname": "手机", "password": "test1234",
    "mobile": "123"})
rec("B8", "非法手机号被拒(400)", body, 400)

body = _post("/admin-api/system/user/create", json={
    "username": uniq("d"), "nickname": "部门", "password": "test1234",
    "deptId": 999999})
rec("B9", "不存在部门被拒(业务码)", body, "err")

body = _put("/admin-api/system/user/update", json={
    "id": 999999, "username": uniq("x"), "nickname": "t"})
rec("B10", "更新不存在用户被拒(业务码)", body, "err")

body = _delete("/admin-api/system/user/delete", params={"id": 999999})
rec("B11", "删除不存在用户被拒(业务码)", body, "err")


print()
print("=" * 72)
print("用例组 C — 角色管理")
print("=" * 72)

body = _get("/admin-api/system/role/page", params={"pageNo": 1, "pageSize": 10})
rec("C1", "角色分页查询成功", body, "ok")

rname = uniq("role")
body = _post("/admin-api/system/role/create", json={
    "name": rname, "code": rname, "sort": 1, "status": 0})
rec("C2", "创建合法角色成功", body, "ok")

body = _post("/admin-api/system/role/create", json={
    "name": rname + "x", "code": rname, "sort": 1, "status": 0})
rec("C3", "重复角色编码被拒(业务码)", body, "err")

body = _post("/admin-api/system/role/create", json={
    "name": "", "code": uniq("rc"), "sort": 1, "status": 0})
rec("C4", "空角色名被拒(400)", body, 400)

body = _post("/admin-api/system/role/create", json={
    "name": "x" * 31, "code": uniq("rc"), "sort": 1, "status": 0})
rec("C5", "角色名31字符被拒(400)", body, 400)

body = _post("/admin-api/system/role/create", json={
    "name": uniq("rn"), "code": uniq("rc"), "status": 0})
rec("C6", "缺少sort被拒(400)", body, 400)

body = _delete("/admin-api/system/role/delete", params={"id": 999999})
rec("C7", "删除不存在角色被拒(业务码)", body, "err")


print()
print("=" * 72)
print("用例组 D — 部门 / 字典")
print("=" * 72)

body = _get("/admin-api/system/dept/list")
rec("D1", "部门列表查询成功", body, "ok")

body = _get("/admin-api/system/dict-type/page", params={"pageNo": 1, "pageSize": 10})
rec("D2", "字典类型分页成功", body, "ok")

body = _get("/admin-api/system/dict-data/page", params={"pageNo": 1, "pageSize": 10})
rec("D3", "字典数据分页成功", body, "ok")


print()
print("=" * 72)
print("用例组 E — 权限控制 / 会话")
print("=" * 72)

body = _post("/admin-api/system/auth/logout")
rec("E1", "登出成功", body, "ok")

old = TOKEN
body = _get("/admin-api/system/user/page", params={"pageNo": 1, "pageSize": 10},
            auth=True)
# 登出后 TOKEN 仍为旧值，需要手动验证旧 token 失效
r = client.get(BASE + "/admin-api/system/user/page",
               params={"pageNo": 1, "pageSize": 10},
               headers={"Authorization": "Bearer " + old, "tenant-id": "1"})
rec("E2", "登出后旧token失效(401)", r.json(), 401)

body = login("admin", "admin123")
rec("E3", "重新登录成功", body, "ok")

body = _get("/admin-api/system/user/page", params={"pageNo": 1, "pageSize": 10},
            tenant="118")
rec("E4", "非默认租户访问应被隔离(非0)", body, "err",
    note="(tenant-id=118 不属于当前会话租户)")


print()
print("=" * 72)
print("用例组 F — 边界 / 一致性观察")
print("=" * 72)

# F1: 分页下限
body = _get("/admin-api/system/user/page", params={"pageNo": 1, "pageSize": 0})
rec("F1", "pageSize=0 被拒(400)", body, 400)

# F2: 分页上限
body = _get("/admin-api/system/user/page", params={"pageNo": 1, "pageSize": 100000})
rec("F2", "pageSize=100000 被拒(400)", body, 400)

# F3: 邮箱长度上界(>50)
body = _post("/admin-api/system/user/create", json={
    "username": uniq("e"), "nickname": "t", "password": "test1234",
    "email": "a" * 45 + "@b.com"})
rec("F3", "邮箱51字符被拒(400)", body, 400)

# F4: 用户名含下划线(创建侧与登录侧规则一致)
body = _post("/admin-api/system/user/create", json={
    "username": "ab_cd", "nickname": "t", "password": "test1234"})
rec("F4", "用户名含下划线被拒(400)", body, 400)

# F5: 密码下界(4位)
body = _post("/admin-api/system/user/create", json={
    "username": uniq("p"), "nickname": "t", "password": "1234"})
rec("F5", "密码4位(下界)创建成功", body, "ok")

# F6: 观察项 — 查询不存在用户返回 code=0 且 data 为空
body = _get("/admin-api/system/user/get", params={"id": 999999})
rec("F6", "查询不存在用户返回明确错误(理想)", body, "err",
    note=f"[观察] 实际code={body.get('code')} data=null，与删除/更新的报错风格不一致")

# F7: 观察项 — 登录账号大小写敏感性
body = login("Admin", "admin123")
rec("F7", "大小写变体账号应视为不同账号(理想)", body, "err",
    note=f"[观察] 实际code={body.get('code')} 用 Admin 登录了 admin 账号")


print()
print("=" * 72)
print(f"汇总：{PASS} 通过 / {PASS + FAIL} 用例，{FAIL} 个失败（含观察项）")
if FAIL:
    print("失败 / 观察项明细：")
    for no, name, expected, code, ok, msg in CASES:
        if not ok:
            print(f"  ✗ {no} {name}  期望={expected} 实际code={code}  {msg}")
print("=" * 72)
