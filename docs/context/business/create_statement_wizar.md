# Create Statement Wizard 功能需求规格说明书

**功能名称：** Create Statement Wizard
**模块：** `tk_freight`
**对象：** `freight.statement.wizard` / `freight.statement.wizard.line`
**适用 Sprint：** Sprint4-4-4
**文档性质：** Functional Requirement Specification
**目的：** 明确定义 Wizard 的生命周期、行数据来源、选择状态、客户过滤、生成前校验及并发安全行为。

---

# 1. 功能定位

Create Statement Wizard 是用户从 **Shipment（货单）** 上创建结算单的临时操作界面。

它的职责只有四件事：

1. 根据当前 Shipment 找出**允许进入结算单的费用服务**；
2. 将这些费用服务转换成 Wizard Line；
3. 允许用户选择/取消选择费用；
4. 用户点击 Generate Statement 后，将用户选择的费用生成 Statement。

Wizard **不是费用的事实来源**。

费用事实仍然来自：

> `freight.service`

费用是否已经被结算使用，仍然由：

> `fee_state`

决定。

Wizard Line 只是一个**临时 UI 快照**。

---

# 2. Wizard 与业务对象关系

必须明确下面的关系：

```text
Shipment
   │
   ├── freight.service 费用
   │       │
   │       ├── service_id
   │       ├── fee_state
   │       ├── customer
   │       ├── amount
   │       └── ...
   │
   ▼
Eligibility Engine
   │
   ▼
Eligible Services
   │
   ▼
Wizard Lines
   │
   ├── service_id      ← 必须真实绑定
   ├── select
   ├── selectable
   ├── snapshot fields
   └── ...
   │
   ▼
User Selection
   │
   ▼
Generate Statement
   │
   ▼
再次校验真实 freight.service
   │
   ▼
Statement
```

核心原则：

> **Wizard Line 不是重新寻找 Service 的地方。**

一旦 Wizard Line 创建成功，它必须知道自己对应的真实：

```text
freight.service
```

因此：

```text
wizard.line.service_id
```

必须是真实关联，而不能在 Generate 时通过：

```text
name + quantity + price
```

重新猜测。

---

# 3. 打开 Wizard

用户在 Shipment 上点击：

> Create Statement

系统创建 Wizard。

假设当前 Shipment：

```text
Shipment S001
```

存在以下费用：

| Service |       Fee | fee_state | Customer   | 是否 eligible |
| ------- | --------: | --------- | ---------- | ----------- |
| S1      |       场站费 | confirmed | Customer A | 是           |
| S2      |       THC | confirmed | Customer A | 是           |
| S3      | Truck Fee | used      | Customer A | 否           |
| S4      |  CAT320D2 | confirmed | Customer B | 否           |

如果当前未选择 customer，则 Wizard 默认展示：

```text
S1
S2
```

不能展示：

```text
S3
S4
```

---

# 4. Eligible 的唯一来源

Wizard 中所有“是否可以进入结算单”的判断必须使用**同一套 eligibility 规则**。

必须存在一个统一判断：

```python
_is_service_eligible(service, customer)
```

它负责判断某个 `freight.service` 是否可以进入当前 Wizard。

其他逻辑不得自己重新实现一套 eligibility。

例如：

```text
_compute_selectable()
```

和：

```text
_eligible_services_for()
```

必须共享同一个 eligibility 判断。

禁止出现：

```text
_compute_selectable() 一套规则
_eligible_services_for() 另一套规则
action_generate_statement() 第三套规则
```

否则以后非常容易出现：

> Wizard 显示可以选，但 Generate 又说不能选。

---

# 5. Wizard Line 创建规则

这是本次重构最重要的部分之一。

## 5.1 创建时必须绑定 service_id

每个 Wizard Line 必须对应一个真实：

```text
freight.service
```

例如：

```text
Wizard Line 1
service_id = S1

Wizard Line 2
service_id = S2
```

而不是：

```text
name = "场站费"
quantity = 1
price = 800
service_id = False
```

---

# 6. 禁止猜测 service_id

旧实现如果存在类似：

```python
search([
    ('name', '=', line.name),
    ('quantity', '=', line.quantity),
    ('price', '=', line.price),
])
```

或者：

```python
name + qty + price
```

寻找原始 Service：

> 必须删除。

原因：

两个费用完全可能：

```text
场站费  800
场站费  800
```

但属于不同 Service。

因此：

> Wizard Line 必须从创建时就保存真实 `service_id`。

Generate 时不允许重新猜。

---

# 7. Wizard 默认选择状态

打开 Wizard 时：

> **所有 eligible Wizard Line 默认 `select=True`。**

例如：

```text
场站费      ☑
THC        ☑
拖车费      ☑
```

用户可以手动取消：

```text
场站费      ☑
THC        ☐
拖车费      ☑
```

最终只有：

```text
select=True
```

的行参与 Generate。

---

# 8. selectable 与 select 是两个不同概念

必须严格区分。

## select

表示：

> 用户现在是否选择这条费用。

它是用户操作状态。

例如：

```text
select = True
```

表示用户勾选。

---

## selectable

表示：

> 当前这条费用是否满足业务条件，可以被用户选择。

例如：

```text
selectable = True
```

表示允许选择。

---

因此：

```text
select = True
selectable = True
```

正常。

但是：

```text
select = True
selectable = False
```

是非法状态。

Generate 时必须明确报错。

---

# 9. 普通 write 不得破坏用户选择

这是本次生命周期重构的核心。

用户操作：

```text
场站费       ☑
THC         ☐
拖车费       ☑
```

服务器收到 write/onchange 等操作后：

> **不能无条件重新把所有 select 设置成 True。**

否则用户刚取消 THC：

```text
THC = False
```

下一次服务器刷新以后又变：

```text
THC = True
```

用户无法正常操作。

所以：

> 普通 Wizard write 必须保留客户端已经提交的 `select` 状态。

---

# 10. 哪些情况下允许重置 select

只有两类情况可以重新建立选择状态。

## 情况 A：客户发生切换

例如：

```text
Customer A
```

切换成：

```text
Customer B
```

此时 eligible 集合发生变化。

必须：

1. 重新计算 eligible services；
2. 重新建立 Wizard Lines；
3. 新集合中的所有 eligible 行：

```text
select=True
```

即：

> 客户切换 = 新的一组候选费用。

---

## 情况 B：服务集合发生重建

如果因为业务条件变化，需要重新建立 Wizard Line 集合：

```text
eligible services changed
```

则：

1. 删除旧 Wizard Line；
2. 按新的 eligible 集合创建；
3. 每一行绑定真实 `service_id`；
4. 新行默认：

```text
select=True
```

---

# 11. 普通 onchange 与“重建”必须区分

这是 Codex 很容易搞错的地方。

不能简单写成：

```python
@api.onchange(...)
def onchange_xxx():
    self.line_ids = rebuild_lines()
```

然后每次 onchange 都：

```text
select=True
```

因为这会导致：

```text
用户取消
 ↓
onchange
 ↓
重建
 ↓
全部重新勾选
```

所以代码必须明确区分：

### 普通更新

```text
保留现有 select
```

和：

### Eligibility 重建

```text
重新建立行
select=True
```

---

# 12. Wizard 行集合必须满足的 invariant

任何时候，只要 Wizard 已完成服务端初始化/重建：

```text
Wizard Lines = Eligible Services
```

也就是说：

> Wizard 不应该保存一堆已经不属于当前 eligible 集合的脏行。

例如：

```text
Eligible:
S1
S2
S3
```

Wizard：

```text
S1
S2
S3
```

必须一致。

---

# 13. 客户过滤

用户可以选择 Customer。

如果：

```text
customer_id = Customer A
```

那么 Wizard 只显示：

> 当前 Shipment + Customer A 对应的 eligible services。

例如：

```text
Shipment S001

Customer A:
S1 800
S2 500

Customer B:
S3 1000
```

选择 Customer A 后：

```text
S1
S2
```

不能出现：

```text
S3
```

---

# 14. customer_id 必须验证归属

Generate Statement 时：

```text
customer_id
```

如果填写，必须满足：

```text
customer_id == shipment.shipper_id
```

或者：

```text
customer_id == shipment.consignee_id
```

否则：

```text
ValidationError
```

例如：

```text
Shipment:
shipper = Customer A
consignee = Customer B

Wizard customer = Customer C
```

必须拒绝。

---

# 15. Generate Statement 前第一轮校验

用户点击：

> Generate Statement

服务器首先处理 Wizard 自身状态。

必须检查：

### 15.1 service_id 存在

每一个 selected line：

```python
line.service_id
```

必须存在。

如果不存在：

> 明确报错。

禁止：

> 根据 name / qty / price 猜测。

---

### 15.2 selected 行必须 selectable

检查：

```python
selected.filtered(lambda x: not x.selectable)
```

如果不为空：

> 报错。

例如：

```text
场站费 ☑ selectable=True
THC   ☑ selectable=False
```

必须拒绝。

不能简单：

```python
selected & eligible
```

然后静默删除 THC。

---

# 16. 为什么不能静默过滤

这是非常重要的用户体验规则。

用户明确勾选：

```text
THC
```

但是服务器发现：

```text
THC 已经被其他 Statement 使用
```

系统不能：

> 偷偷把 THC 删除，然后生成剩余费用。

必须告诉用户：

> “费用 THC 已不可选择，请刷新向导后重新操作。”

原因：

否则用户看到的：

```text
800 + 500 = 1300
```

最终可能只生成：

```text
800
```

用户会不知道为什么。

---

# 17. FOR UPDATE 后必须重新校验

这是第二层安全机制。

Generate 时：

```text
第一次 eligibility 校验
        ↓
获取数据库行锁 FOR UPDATE
        ↓
再次读取真实 freight.service
        ↓
重新进行完整 eligibility 校验
        ↓
创建 Statement
```

不能：

```text
第一次检查 OK
↓
FOR UPDATE
↓
只检查 fee_state
↓
生成
```

---

# 18. 锁后必须重新检查什么

至少包括：

### 18.1 fee_state

费用是否仍然可以使用。

---

### 18.2 invoiced

费用是否已经进入发票流程。

---

### 18.3 Statement 占用

是否已经被非 voided Statement 使用。

---

### 18.4 shipment 归属

Service 是否仍属于当前 Shipment。

---

### 18.5 customer 归属

Service 是否仍符合当前 customer。

---

### 18.6 其他 eligibility 条件

必须重新执行：

```python
_is_service_eligible(service, customer)
```

而不是自己复制一套条件。

---

# 19. 并发场景

必须考虑两个用户同时打开 Wizard。

例如：

```text
User A 打开 Wizard
User B 打开 Wizard
```

两个人看到：

```text
场站费 800
```

都可以选择。

User A：

```text
Generate
```

成功。

User B：

```text
Generate
```

此时不能继续生成第二个 Statement。

User B 必须在锁后重新校验时发现：

```text
fee_state / statement occupation
```

已经发生变化。

最终：

```text
ROLLBACK + ValidationError
```

---

# 20. Generate 的最终数据来源

这是另一个关键原则。

Generate Statement 时：

> Wizard Line 负责告诉系统“用户选择了谁”。

但：

> **真正的费用数据必须重新从 `freight.service` 获取。**

即：

```text
Wizard Line
    ↓
service_id
    ↓
freight.service
    ↓
创建 Statement Line
```

不能把 Wizard 中用户提交的：

```text
name
qty
price
tax
```

直接当作最终业务事实。

Wizard 是 snapshot / UI 层。

Service 才是费用事实来源。

---

# 21. Snapshot 字段

Wizard 可以保存：

```text
name
quantity
price
tax_amount
settlement_rate
```

用于 UI 展示。

其中：

```text
tax_amount
settlement_rate
```

必须 readonly。

这些字段是：

> Wizard snapshot。

不是用户可以修改的费用事实。

---

# 22. Statement Line sequence

生成 Statement Line 时：

```text
10
20
30
40
...
```

依次递增。

不能使用随机顺序。

Wizard 中的费用顺序应稳定。

---

# 23. Wizard 的完整生命周期

整个生命周期应该严格表现为：

```text
① 打开 Shipment
       ↓
② 点击 Create Statement
       ↓
③ 计算 eligible services
       ↓
④ 创建 Wizard Lines
       ↓
⑤ 每条 line 绑定 service_id
       ↓
⑥ 所有 eligible line 默认 select=True
       ↓
⑦ 用户取消不需要的费用
       ↓
⑧ 普通 write/onchange
       ↓
⑨ 保留 select 状态
       ↓
⑩ 用户点击 Generate
       ↓
⑪ customer 校验
       ↓
⑫ selected service_id 校验
       ↓
⑬ selected selectable 校验
       ↓
⑭ FOR UPDATE
       ↓
⑮ 从数据库重新读取 service
       ↓
⑯ 完整 eligibility 校验
       ↓
⑰ 创建 Statement Draft
       ↓
⑱ 写回费用占用状态
       ↓
⑲ 完成
```

---

# 24. 客户切换生命周期

例如：

```text
第一次：

Customer A

☑ 场站费
☑ THC
☑ Truck
```

用户切换：

```text
Customer B
```

系统必须：

```text
重新计算 Customer B eligible services
        ↓
删除/重建 Wizard Lines
        ↓
每个新 line 绑定真实 service_id
        ↓
所有新 eligible line = select=True
```

不能保留：

```text
Customer A 的旧费用
```

---

# 25. 错误生命周期

如果 Wizard 出现：

```text
service_id = False
```

并且无法从当前上下文合法绑定：

> 不允许猜测。

直接：

```text
ValidationError
```

提示用户：

> “结算向导中的费用关联已失效，请关闭并重新打开向导。”

---

# 26. 明确禁止的实现方式

Codex 不允许采用以下实现。

### 禁止 1：name+qty+price 找 Service

```python
search([
    ('name', '=', line.name),
    ('quantity', '=', line.quantity),
    ('price', '=', line.price),
])
```

---

### 禁止 2：每次 onchange 都全部 select=True

```python
for line in lines:
    line.select = True
```

导致用户取消选择后又被重新选中。

---

### 禁止 3：Generate 时静默过滤 selected

```python
selected = selected.filtered(...)
```

然后继续生成。

必须明确报错。

---

### 禁止 4：锁后只检查 fee_state

必须完整执行 eligibility。

---

### 禁止 5：Wizard 自己复制 eligibility 规则

所有 eligibility 必须进入：

```python
_is_service_eligible()
```

---

### 禁止 6：直接相信 Wizard snapshot

Generate 时最终费用必须回到：

```text
freight.service
```

---

# 27. 这次重构到底改什么

这一点建议直接写进 Codex 的任务说明里。

**Sprint4-4-4 不是重新设计 Create Statement。**

它主要解决原 Wizard 的五个生命周期问题：

### 问题 1：Wizard Line 没有稳定身份

旧：

```text
Wizard Line
  ↓
name / qty / price
  ↓
Generate 时猜 Service
```

新：

```text
Wizard Line
  ↓
service_id
  ↓
真实 Service
```

---

### 问题 2：用户取消选择会被服务器重置

旧：

```text
用户取消
 ↓
onchange/write
 ↓
重建
 ↓
全部 select=True
```

新：

```text
普通 write/onchange
 ↓
保留 select
```

只有：

```text
客户切换
```

或：

```text
eligible 集合真正重建
```

才重新默认全选。

---

### 问题 3：selectable 只是展示字段，没有真正约束 Generate

旧：

```text
selectable=False
select=True
 ↓
仍然可能 Generate
```

新：

```text
select=True
+
selectable=False
 ↓
明确拒绝
```

---

### 问题 4：并发锁后检查不完整

旧：

```text
检查
 ↓
FOR UPDATE
 ↓
只检查 fee_state
 ↓
生成
```

新：

```text
检查
 ↓
FOR UPDATE
 ↓
重新读取 Service
 ↓
完整 eligibility
 ↓
生成
```

---

### 问题 5：eligibility 有多个版本

旧：

```text
_compute_selectable()
       ≠
_eligible_services_for()
       ≠
Generate 校验
```

新：

```text
                  ┌─────────────────────┐
                  │ _is_service_eligible│
                  └──────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
       selectable       eligible list    Generate
```

**一个规则，三个地方调用。**

---

# 28. Codex 执行前必须先回答的问题

在真正修改代码以前，Codex 必须先回答下面 10 个问题。

1. 当前 `freight.statement.wizard.line` 的 `service_id` 是在哪里创建的？
2. 当前代码什么时候会重新构造 `wizard.line`？
3. 当前代码什么时候会把 `select` 重置成 True？
4. 用户取消 checkbox 后，哪个 `write/onchange/create` 会影响它？
5. 当前代码是否存在 `name + qty + price` 恢复 service_id？
6. 当前 `selectable` 是在哪里计算的？
7. 当前 `eligible_services` 是在哪里计算的？
8. 两者是否存在重复 eligibility 逻辑？
9. `action_generate_statement()` 在 `FOR UPDATE` 后目前检查了什么？
10. Generate 最终创建 Statement Line 时，数据究竟来自 Wizard 还是重新读取 `freight.service`？

**如果 Codex 无法逐项回答，不允许开始编码。**

---

# 29. 最终验收场景

至少必须通过以下场景。

### Case 1：默认全选

打开：

```text
3 条 eligible
```

结果：

```text
☑
☑
☑
```

---

### Case 2：取消一条

用户：

```text
☑
☐
☑
```

普通 onchange/write 后仍然：

```text
☑
☐
☑
```

---

### Case 3：客户切换

Customer A：

```text
A1
A2
```

切换 Customer B：

```text
B1
B2
B3
```

不得残留：

```text
A1
A2
```

并且：

```text
B1 B2 B3
```

默认全部勾选。

---

### Case 4：不可选择费用被勾选

```text
select=True
selectable=False
```

Generate：

> 必须失败并明确提示。

---

### Case 5：并发占用

A、B 同时打开。

A 先 Generate。

B 再 Generate：

> 必须被锁后 eligibility 校验拦截。

---

### Case 6：service_id 缺失

Wizard Line：

```text
service_id=False
```

Generate：

> 明确错误。

不得通过：

```text
name + qty + price
```

寻找。

---

### Case 7：非法 customer

Shipment：

```text
shipper=A
consignee=B
```

Wizard：

```text
customer=C
```

Generate：

> 必须拒绝。

---

# 30. 给 Codex 的执行指令

最后我建议你**不要把原来的 Intent 直接重新扔给 Codex**，而是：

> **Intent 契约 + 本功能需求规格 = 编码依据。**

给 Codex 的指令可以直接这样写：

```text
你现在不要修改代码。

请先阅读：

1. Sprint4-4-4 Intent Contract
2. Create Statement Wizard 功能需求规格
3. 当前 freight_statement_wizard.py
4. freight_statement_wizard_view.xml
5. Sprint4-4-2 / Sprint4-4-3 中与 fee_state、eligibility、Statement generation 相关代码

本次任务的第一阶段只有代码审查，不允许写代码。

请回答：

A. 当前 Wizard 的真实生命周期是什么？
B. Wizard Line 在哪里创建？
C. service_id 当前如何获得？
D. 是否存在 name+qty+price 猜测恢复？
E. select 当前在哪里被设置/重置？
F. 普通 write/onchange 是否会破坏用户 select 状态？
G. customer 切换如何重建 Wizard Lines？
H. selectable 当前如何计算？
I. eligible_services 当前如何计算？
J. 是否存在两套 eligibility 规则？
K. Generate 前检查什么？
L. FOR UPDATE 后检查什么？
M. Generate 最终使用 Wizard 数据还是 freight.service 数据？

然后输出：

1. 当前实现流程图
2. 当前代码与功能需求的差异表
3. 每个差异对应的文件、方法、代码位置
4. 本 Sprint 必须修改的最小代码范围
5. 明确哪些代码不应该修改

禁止在本阶段修改任何文件。

只有完成上述分析并确认差异后，才能进入编码阶段。
```

---

## 我认为这一步非常关键

你前面说：

> **“codex 做了一下午，我实测还有各种错误，而且我始终没看懂对 wizard 做了哪些重构。”**

我现在基本可以解释为什么会这样。

你原来的 Intent 是**“告诉 Codex 必须达到什么治理结果”**，但缺少**“Wizard 到底怎么活”**。

对于这种 Odoo Wizard，最重要的不是先讲 B-61、B-62、B-63，而是先把这条生命周期钉死：

```text
真实 Service
     ↓
Eligibility
     ↓
Wizard Line
     ↓
service_id 永久绑定
     ↓
select 默认全选
     ↓
用户取消
     ↓
普通 write 保留取消状态
     ↓
客户改变 → 重新建立候选集合
     ↓
Generate
     ↓
锁真实 Service
     ↓
重新 Eligibility
     ↓
生成 Statement
```

