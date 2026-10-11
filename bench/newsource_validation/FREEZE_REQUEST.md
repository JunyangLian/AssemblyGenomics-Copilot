# 十二题答案冻结确认范围

目前状态为draft。此文件是审核请求，不是FROZEN文件，也不表示用户已经授权。

外部有答案材料AI复核一致12/12（用户转述）；Linux/Windows题库12题、72文件逐字节一致。原题目、候选答案与构题前协议未改。

| 题号 | 判定 | 可见缺陷 | 根因 | expected SHA-256 |
|---|---|---|---|---|
| qc_001 | block | gff_faa_link_missing | id_mismatch | 21ac62d2232958466f3329db51a044703fa6e5fa9a8f132845dff79cabcade1c |
| qc_002 | pass | none | none | 67dffeeb39afb0f7d471a520e98dcd0e70883828c95e280abe06d4326818bb3e |
| qc_003 | block | gff_hierarchy_inconsistent | gff_hierarchy_error | 802ccfdf11757fd6bdc035b82ae4024172260a6770abf3e6067a8496aa4d1e14 |
| qc_004 | block | gff_reference_unresolved | gff_hierarchy_error | f71739b21b589baeeac10639b9c5ee2eecaf68fc11457e0cbd8e32233de65dbf |
| qc_005 | pass | none | none | 883b2d4732c930f0e2aeaaf258fce2dd4602b54a4edfdb32958a5a74ae434827 |
| qc_006 | block | gff_faa_link_missing | id_mismatch | dbbd1450cdd4acaa1494cd93fb9c7a2d222450702b17cb5e2f68d630d69f352d |
| qc_007 | block | gff_reference_unresolved | gff_hierarchy_error | de18478be6c05e19c87832c1fdea90de0ffa586aef1e70a13db105cc49683395 |
| qc_008 | pass | none | none | 8b812875a0ff035f8f66182cbf0ef09020fb633e5b4f6a0ecac930d87a1412de |
| qc_009 | block | gff_hierarchy_inconsistent | gff_hierarchy_error | 361e063d8c80396ac30e0ad2a875b1335f9c076c97dd823d670082fcdcc51800 |
| qc_010 | pass | none | none | 0607e5688a7f0b0edfecc529a3ee572f7a2baa73367d662c69969bac27eb8991 |
| qc_011 | pass | none | none | e35165d3e1212e209ef721255f22167fafd10046c464ecf95ebb5abd2242a269 |
| qc_012 | pass | none | none | 7e575c919aeba6193e3dc7c7a8d38fddd27e037f6ffb340fe0eade585710bd56 |

确认后的范围：登记上述十二份expected的SHA到FROZEN.md/json，并绑定公共合同、锁定协议、Linux验收及外部材料复核记录。不会重写原expected/meta的draft字节；用户确认通过授权侧录表达，保留已验证的跨平台身份。

确认不包含新增API调用或付费预算。模型身份、累计请求/token保护、价格与预算须单独准备；不继承旧额度。当前试验只作十二题的描述性验证，未填写门槛，不能宣布历史H1–H3成立。

仍需保留：外部AI不是盲审/真人审核，评审模型和运行原稿未知；完整gzip未供外部核验；复现是相同真实子集生成，不是完整来源的独立重提取；机制已在项目开发中用过，基础模型暴露未知。

## 确认对象的记录身份

- CASE_MANIFEST.json: 835fa39b3d72b9674930fc36d5f4bc3476e94b94b2b60a1660a0d5e32cb9006f
- PROTOCOL_LOCK.json: 255c6b3f114132948136ea7e2e7d08251527fc6b61b0d92e7f90d6f687fc72ad
- LINUX_REPRODUCTION.json: 75e8cc6c60e327bea1ab534605d1ace34a21d61b0a5d45c205f83fa3f920343d
- review/EXTERNAL_AI_REVIEW.json: ce014516b6982de869b907206f86006dcae35c0ff443d40b8631ed6c260fec61
