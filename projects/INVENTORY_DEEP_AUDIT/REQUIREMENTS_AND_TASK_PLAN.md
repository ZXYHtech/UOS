# Inventory Lite 深度审计｜需求大纲与任务计划

> 目标：不是只回答“现在有没有库存功能”，而是从源码、数据模型、业务闭环、研发生产适配、经营管理、开源成熟方案、架构演进、体验与自动化等层面，判断这套系统能否逐步成长为适合小型电子产品公司的业务操作系统。

## 1. 已确认的当前系统基础（仅作为审计起点，不代表最终结论）

当前仓库已经覆盖登录与角色权限、人员/仓库/物料/平台账号、库存与库存流水、安全库存预警、截图识别与人工确认、订单/发货、跨仓调货、操作日志、导入导出、采购与成本、BOM、商品价格与资料、商品分类审核、货位/仓库平面、淘宝/平台适配、备份恢复、PC Web、移动端 PWA、离线移动端和 Android WebView 等能力。后端主体由 Python 标准库 HTTP API + SQLite 构成，并预留 PostgreSQL 边界。

这意味着本项目不应按“重写一个库存系统”的思路开展，而应先判断：
1. 哪些能力已经真正形成闭环；
2. 哪些只是页面、字段或局部流程；
3. 哪些功能对于电商电子产品研发生产销售场景仍然缺失；
4. 哪些地方已经接近 ERP/MRP/WMS/PLM/售后系统的边界；
5. 哪些能力应继续自研，哪些更适合借鉴或集成成熟开源方案。

## 2. 需求总纲

### A. 源码与当前功能事实审计
- 固定仓库 commit，避免分析过程中代码漂移。
- 建立代码/文档/API/数据库/UI/状态机/权限的完整地图。
- 对照 README、开发索引和实际实现，区分“已实现 / 部分实现 / 占位 / 仅文档存在”。
- 识别 `server.py`、`services.py`、`database.py`、`recognition.py` 等大型核心文件的职责边界、耦合和长期维护风险。

### B. 业务完整性审计
- 库存：现存、可用、预留、占用、在途、报废、冻结、样品、研发库存、盘点、批次/序列号。
- 仓储：仓库、库位、上架、拣货、移库、盘点、扫码、批量作业。
- 采购：供应商、询价、采购单、到货、部分收货、退货、MOQ、交期、价格阶梯、供应商绩效。
- 订单履约：渠道订单、人工订单、库存分配、缺货、拆单、拣配发货、取消、异常。
- 调货：调出、在途、收货、差异、合并、回滚与日志。
- 商品主数据：SKU/料号、别名、分类、属性、单位、生命周期、资料与图片。
- 定价与利润：采购成本、标准成本、成交价、渠道价格、费用、毛利、贡献利润。

### C. 电子产品研发与生产适配
重点判断当前系统是否能够承接：
- MPN / 厂商 / 封装 / 参数 / 数据手册 / 供应商料号等电子料主数据；
- AVL、替代料、优选料、停产/EOL、缺料替代；
- EBOM、MBOM、多级 BOM、BOM 版本、Reference Designator；
- 研发版本、ECN/ECO、图纸/固件/测试文档版本控制；
- 样机、实验室库存、工程领料、研发退料；
- MRP、缺料运算、采购建议、安全库存与交期；
- 生产工单、齐套、领料、退料、报废、完工入库；
- IQC/IPQC/FQC/OQC、NCR、隔离、返工、报废；
- 批次/序列号、成品与物料追溯；
- RF/电性能测试记录、测试报告、固件版本、设备与校准；
- 委外加工、客供/寄售、加工费；
- 标准成本、实际成本、损耗、人工、制造费用和差异分析。

### D. 电商、销售、售后与经营
- 多平台/多店铺订单与库存同步；
- SKU 映射、渠道库存发布、取消/退款/发货状态对账；
- 询盘、报价、样品、客户等级价、销售跟进；
- 退换货、RMA、维修、质保与序列号售后历史；
- 平台费用、支付费用、运费、税费、退款后的真实贡献利润；
- 销量趋势、库存周转、呆滞、缺货率、采购交付、履约 SLA、现金占用和产品评分。

### E. 开源系统洞察
至少覆盖四类：
1. ERP/MRP：ERPNext、Odoo Community、Dolibarr、Tryton 等；
2. 电子料/BOM：InvenTree、Part-DB、OpenPnP 生态等；
3. WMS：OpenBoxes 以及当前仍活跃的开源 WMS；
4. 电商/订单：Saleor、Medusa 等可借鉴的开放架构。

对标不是为了“换系统”，而是回答：
- 它们有哪些成熟能力是当前系统明显缺失的；
- 哪些架构模式、数据模型、工作流可以直接借鉴；
- 哪些功能对当前团队而言过度设计；
- 哪些能力应该自研，哪些应该通过插件/API 集成。

### F. 技术架构、安全与运维
- SQLite 与未来 PostgreSQL 的真实迁移难点；
- 并发、事务、幂等、后台任务、队列、缓存、分页、海量流水；
- 身份认证、会话、默认账号、凭据、文件上传、备份安全；
- 审计日志防篡改、最小权限、仓库级对象权限；
- 自动化测试、数据库迁移测试、状态机测试、安全测试、负载测试；
- 日志、指标、报警、RPO/RTO、灾备和恢复演练。

### G. 使用体验与自动化
- PC 信息架构与高频操作效率；
- 移动端拍照、扫码、拣货、盘点、收货、调货；
- 离线模式和同步冲突；
- 全局搜索、模糊匹配、MPN/别名搜索、条码/二维码；
- 规则引擎：缺货、补货、异常、审批、分类、对账、提醒；
- AI Copilot：OCR、SKU 匹配、异常检测、自然语言查询、采购建议、报告自动生成。

## 3. 最终必须回答的核心问题

最终报告必须明确给出判断，而不只是列功能：
- 现在这套系统处于“库存工具 / 轻量 WMS / 电商订单库存系统 / 轻量 ERP / 可继续演进的平台”中的哪个阶段？
- 对一个做电子产品研发、采购、生产、仓储、电商销售和售后的团队，当前已经满足多少关键闭环？
- 哪些缺口会造成真实的错账、缺料、追溯失败、生产混乱或利润判断错误？
- 哪些缺口属于近期必须补，哪些可等业务规模上升后再做？
- 是继续保持轻量单体更合适，还是需要逐步模块化？
- PostgreSQL、后台队列、插件系统、事件总线、搜索服务等分别在什么业务规模下才值得引入？
- 哪些成熟开源系统值得“借鉴模块/数据模型/API”，而不是整体替换？
- 如何在不破坏现有可用功能的情况下，逐步演进到更完整的 R&D + ERP/MRP + WMS + 电商经营体系？

## 4. 评分框架

所有关键结论建议按 0–5 分成熟度评估，并附源码或研究证据：
- 功能完整性
- 数据一致性
- 状态闭环
- 权限与审计
- 研发适配
- 生产适配
- 仓储效率
- 电商适配
- 销售/售后适配
- 经营分析
- 自动化程度
- 可维护性
- 可扩展性
- 安全与可靠性
- 用户体验

同时给出：业务影响、发生概率、实施难度、依赖、短期收益、长期价值。禁止用没有证据的“90% 完成”之类数字制造精确感。

## 5. 证据要求

每个任务输出至少包含：
1. 审计对象和范围；
2. 代码/Schema/API/UI/文档证据；
3. 当前真实行为；
4. 问题或能力缺口；
5. 对电商电子产品研发生产销售的业务影响；
6. 可借鉴的成熟模式；
7. 改进方案；
8. 优先级与依赖；
9. 风险和迁移注意事项；
10. 可验证的验收信号。

开源研究必须记录项目主页/仓库、版本或发布日期、许可证、活跃度证据、相关模块，并区分“当前事实”和“建议借鉴”。

## 6. 任务分波次

### W0｜审计入口与外部对标入口

- `TASK_INV_AUDIT_REPO_SNAPSHOT_01` — Pin repository snapshot and build source/document inventory
- `TASK_INV_AUDIT_OSS_LANDSCAPE_01` — Build current open-source inventory/ERP/WMS/electronics systems landscape

### W1｜当前系统事实地图

- `TASK_INV_AUDIT_CAPABILITY_MAP_01` — Create current capability and workflow matrix
- `TASK_INV_AUDIT_DATA_MODEL_01` — Audit database schema, entities, relationships and lifecycle states
- `TASK_INV_AUDIT_API_PERMISSION_01` — Audit API surface, authentication, authorization and warehouse data scope
- `TASK_INV_AUDIT_FRONTEND_UX_MAP_01` — Map PC, mobile and offline user journeys and interaction debt
- `TASK_INV_AUDIT_CODE_ARCHITECTURE_01` — Audit source architecture, module boundaries and maintainability hotspots
- `TASK_INV_AUDIT_DOC_TRUTH_01` — Check documentation-to-code truth alignment

### W2｜库存/采购/订单/平台等核心业务

- `TASK_INV_AUDIT_STOCK_MODEL_01` — Audit inventory quantity model and stock semantics
- `TASK_INV_AUDIT_WAREHOUSE_LOCATION_01` — Audit multi-warehouse, bin, shelf and physical inventory capabilities
- `TASK_INV_AUDIT_PROCUREMENT_01` — Audit supplier, purchase order and receiving workflow
- `TASK_INV_AUDIT_ORDER_FULFILLMENT_01` — Audit order allocation, picking, shipping and completion workflow
- `TASK_INV_AUDIT_TRANSFER_01` — Audit inter-warehouse transfer and in-transit control
- `TASK_INV_AUDIT_MASTER_DATA_01` — Audit product master data, aliases, categories, units and lifecycle
- `TASK_INV_AUDIT_BOM_COST_01` — Audit BOM, bundle and product cost capabilities
- `TASK_INV_AUDIT_PRICING_MARGIN_01` — Audit pricing, channel price and margin management
- `TASK_INV_AUDIT_IMPORT_EXPORT_BACKUP_01` — Audit import, export, backup and restore safety
- `TASK_INV_AUDIT_OCR_AI_01` — Audit OCR/AI recognition pipeline and human confirmation controls
- `TASK_INV_AUDIT_PLATFORM_CONNECTOR_01` — Audit marketplace/platform account and SKU mapping integration
- `TASK_INV_AUDIT_DASHBOARD_KPI_01` — Audit dashboard, alerts and decision-support metrics
- `TASK_INV_AUDIT_EXCEPTION_AUDITLOG_01` — Audit exception handling and operation log completeness

### W3｜电子产品研发与生产适配

- `TASK_INV_AUDIT_PART_PARAMETRIC_01` — Assess electronics component parametric master-data fitness
- `TASK_INV_AUDIT_AVL_SUBSTITUTE_01` — Assess AVL, alternate parts and substitute management
- `TASK_INV_AUDIT_REVISION_ECN_01` — Assess part revision, BOM revision and ECN/ECO change control
- `TASK_INV_AUDIT_EBOM_MBOM_01` — Assess engineering BOM to manufacturing BOM flow
- `TASK_INV_AUDIT_PROTOTYPE_SAMPLE_01` — Assess prototype, sample and engineering-stock workflows
- `TASK_INV_AUDIT_MRP_01` — Assess MRP, shortage explosion and replenishment planning
- `TASK_INV_AUDIT_WORK_ORDER_01` — Assess production work orders, kitting, issue/return and completion
- `TASK_INV_AUDIT_LOT_SERIAL_TRACE_01` — Assess lot, serial number and end-to-end traceability
- `TASK_INV_AUDIT_QC_NCR_01` — Assess incoming, in-process and final quality workflows
- `TASK_INV_AUDIT_TEST_RECORD_01` — Assess product test data, calibration and equipment traceability
- `TASK_INV_AUDIT_DOC_CONTROL_01` — Assess drawings, datasheets, firmware and controlled-document linkage
- `TASK_INV_AUDIT_SUBCONTRACT_01` — Assess outsourced processing and consigned-material workflows
- `TASK_INV_AUDIT_COST_ACCOUNTING_01` — Assess actual manufacturing cost and variance accounting

### W4｜电商、销售、售后与经营

- `TASK_INV_AUDIT_OMNICHANNEL_01` — Assess omnichannel order, inventory and SKU synchronization
- `TASK_INV_AUDIT_CRM_QUOTE_01` — Assess inquiry, quotation, sample and customer-specific sales workflow
- `TASK_INV_AUDIT_FORECAST_REPLENISH_01` — Assess demand forecast and intelligent replenishment
- `TASK_INV_AUDIT_RETURNS_RMA_01` — Assess returns, refund, RMA, repair and warranty lifecycle
- `TASK_INV_AUDIT_CUSTOMER_SERVICE_01` — Assess customer-service tickets and operational exception collaboration
- `TASK_INV_AUDIT_CHANNEL_FINANCE_01` — Assess channel settlement, fees, shipping cost, tax and contribution margin
- `TASK_INV_AUDIT_PRODUCT_INTELLIGENCE_01` — Assess product portfolio and commercial intelligence model
- `TASK_INV_AUDIT_EXEC_REPORTING_01` — Assess owner/manager reporting and operational cockpit

### W5｜架构、安全、可靠性、体验与自动化

- `TASK_INV_AUDIT_SCALABILITY_01` — Assess scalability, concurrency and SQLite-to-PostgreSQL evolution
- `TASK_INV_AUDIT_SECURITY_01` — Perform security and secrets review
- `TASK_INV_AUDIT_RELIABILITY_DR_01` — Assess reliability, backup, restore, recovery and business continuity
- `TASK_INV_AUDIT_TESTING_OBSERVABILITY_01` — Audit automated tests, migrations, logging and observability
- `TASK_INV_AUDIT_UX_HEURISTICS_01` — Perform detailed desktop UX and information-architecture review
- `TASK_INV_AUDIT_MOBILE_OFFLINE_SYNC_01` — Assess mobile, PWA, offline and synchronization experience
- `TASK_INV_AUDIT_SEARCH_SCAN_01` — Assess global search, barcode/QR and fast warehouse interaction
- `TASK_INV_AUDIT_AUTOMATION_RULES_01` — Design rules engine and event-driven automation opportunities
- `TASK_INV_AUDIT_AI_COPILOT_01` — Design AI copilot and agent automation opportunities

### W6｜开源深度对标与差距矩阵

- `TASK_INV_AUDIT_OSS_ERP_01` — Deep benchmark open-source ERP suites
- `TASK_INV_AUDIT_OSS_ELECTRONICS_01` — Deep benchmark electronics parts/BOM systems
- `TASK_INV_AUDIT_OSS_WMS_01` — Deep benchmark open-source WMS and warehouse systems
- `TASK_INV_AUDIT_OSS_COMMERCE_01` — Deep benchmark open-source commerce/order systems
- `TASK_INV_AUDIT_OSS_ARCH_PATTERN_01` — Extract reusable architecture and extension patterns from open-source peers
- `TASK_INV_AUDIT_GAP_MATRIX_01` — Build weighted current-system vs target-needs vs open-source gap matrix

### W7｜目标架构、路线图与最终报告

- `TASK_INV_AUDIT_UX_AUTOMATION_BACKLOG_01` — Create prioritized UX and automation improvement backlog
- `TASK_INV_AUDIT_TARGET_ARCHITECTURE_01` — Design target architecture options for next-stage evolution
- `TASK_INV_AUDIT_ROADMAP_01` — Build 0-3-6-12-24 month product and technical roadmap
- `TASK_INV_AUDIT_IMPLEMENTATION_BACKLOG_01` — Convert recommendations into implementation-ready epics and stories
- `TASK_INV_AUDIT_FINAL_REPORT_01` — Produce final deep audit and strategic recommendation report

## 7. 预期输出体系

项目采用“多个专题报告 + 一个总报告”的方式，不把全部分析塞进一个超长文件。主要输出包括：
- 当前系统事实地图；
- 数据模型与状态机审计；
- API/权限/安全审计；
- 库存/仓储/采购/订单/调货/平台能力审计；
- 电子产品研发适配报告；
- 生产/MRP/质量/追溯报告；
- 电商/销售/售后/利润分析报告；
- PC/移动/离线 UX 报告；
- 自动化规则与 AI Copilot 机会清单；
- 开源 ERP/WMS/电子料/电商对标报告；
- 证据化 Gap Matrix；
- Target Architecture；
- 0–3–6–12–24 个月路线图；
- 可直接转开发的 Epic/Story Backlog；
- 最终深度审计与战略建议报告。

## 8. 优先级原则

建议排序：
1. 先解决会造成库存、订单、采购、成本或权限错误的问题；
2. 再补研发生产闭环和可追溯性；
3. 再提升仓储、电商和售后效率；
4. 再做经营洞察、自动化与 AI；
5. 架构升级必须由真实负载和业务复杂度触发，不为了“技术先进”提前复杂化。

## 9. 本阶段边界

本项目是**只读深度审计与规划阶段**。`ZXYHtech/inventory` 作为外部证据仓库读取，不在本项目中直接改源码。所有报告写入 UOS 的 `projects/INVENTORY_DEEP_AUDIT/`。审计完成后，可基于最终 Backlog 再新建“Inventory Implementation”项目进入逐项开发、迁移和验证。
