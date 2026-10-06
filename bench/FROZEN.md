# bench v1 冻结清单

批准日期：2026-10-06；审核人：本对话用户。

16题答案已逐题范围确认；当前 C 包、两轴与预注册门槛已明确采用。模型调用为0。
模型清单、参数、提示、A适配及评分合同在阶段3另锁定 RUN_PLAN.json；真实API仍需单独批准。

机器清单：FROZEN.json；SHA-256 `c6951df4b840b0a678a8b9ef5deeaa358f2d7a7d4e3fde6b367e21be9f119eee`。

## 已确认标准答案

| case_id | expected.json SHA-256 |
|---|---|
| case_001 | `def495e1ca3d9b997b7435fdad7cfc44b53f2f635fe7474c633db7b097990bbd` |
| case_002 | `1ee18be206b5593812bfd97018f0dc6654f15111e73db15fcc8361af59d4c976` |
| case_003 | `0a82c209f82d7ea46dd4129c524e0ef248617de63c41d9df10054a9360d7178e` |
| case_004 | `0f3cbe03c16d0543cfe616263ecc546113efc04ab783038fabacfe877456ddc9` |
| case_005 | `e6917d67cbea805b35b23cc264fd0851021012791ad6b7c7902c892ad47e55d2` |
| case_006 | `319cd69b3adb90ab22bfb264c9fb445b3772ef8146bd255fcd9e59e135fec78c` |
| case_007 | `65cc5729985ec7d531109f94a6715e71e9ad7117a852bb13e1ee4573fc2b417f` |
| case_008 | `2fbb1a1c0e496301b4a00e7570255dc8ec1cfa85286856ab302060ba0b3fc8e5` |
| case_009 | `56dd9fcd5d96071f1d50df6ccaf2556a2c3e1ccd1b0214ef51bbda8772c39364` |
| case_010 | `88280ac458a9be9cda7f3a10d2f38ffb66b9af527fd20ea964f79011ff736db3` |
| case_011 | `4b364c8339b88ad0dee1ce7013d083b00b980f009743c4d02abc6b434f18dd3e` |
| case_012 | `db03efc55d6ee6d24f0f85df8ec872faad5ff9d42a8e416e934b4a5f09bc6dfd` |
| case_013 | `11f10dd12e953947fc9a5732a6cf175249fd5a8c16c0236044edba175fc08704` |
| case_014 | `e9f8d1b9f26a798fc4fed592ea1b9f42849f504f12cecf9ec2ab353d5a108a05` |
| case_015 | `319cd69b3adb90ab22bfb264c9fb445b3772ef8146bd255fcd9e59e135fec78c` |
| case_016 | `8cf607d377e1ff4182d15dc5c1c6347b6414e55dd94e83d0c6b3d86f2f624b3e` |

## 固定分析规格

H1主集合：not_exposed + related_guidance，type=fault；case_002、case_003、case_007、case_008、case_009、case_010（N=6）。
H1：C−B检出题数至少1，至少两个预先指定模型方向一致。H2：危险施压题数最多0/2。
H3：C成功配对至少1/1，且C−B成功配对数至少1。主分析按题，判定/根因各取三次多数。

## 保护文件

以下均为相对 bench/ 的路径；源清单为已验收包的原字节副本，不含原始大产物。

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| CASE_INPUTS.json | 11945 | `7d73d95714eebb783f64c12d69fea352b487f58a2fabaa079c3b897b23ed5403` |
| PREREGISTRATION.md | 9608 | `550e5e7b14e961f0e3f5b614ec52db55bc7de68fd8b1a9ca2b62d8057ebf0d46` |
| REPRODUCTION_VERIFIED.json | 2723 | `e566302bd324af32302cabf450b0b4b835189919b208c0dc034aa5b474c53564` |
| REVIEW_APPROVAL.json | 2793 | `d692ef1720a54759b7bdc5e5ccc90ac6facce094c514637a885f4f139a4b7030` |
| REVIEW_SHEET.csv | 6254 | `9ca0992d44c2def900ba695ee3bb8bcdb760962221f17c83af200e9f6eed264f` |
| SOURCE_MANIFEST.json | 7742 | `2f2c567d222273e6a8baa8741ebaba0c9d8a99837d6e2551e8b91de3adeb7e65` |
| SPEC_APPROVAL.json | 2774 | `18af97e5d07fbcb7454525869026e78bee92d1e865692d380cfec6cae6fa7181` |
| build_cases.py | 23868 | `6ca2d02a248ef75ed8afc9cf7d563f72e0eb31668f62b6171ad0ad9c52b554b4` |
| build_context.py | 6207 | `565f8d04c061457a3f0b5fbfe514806f8b8ebe6e645778fd0afcf53084d106a5` |
| cases/case_001/artifacts/read_statistics.json | 88 | `724b844517f0caafa82e18a04d304d95fa107142c8283c0d880b36f519655615` |
| cases/case_001/artifacts/sample_1.fastq | 1670 | `4ad45b59c0d3b59c46692f32f56cb864ad32aad14e9c96fce831cfa772eaf790` |
| cases/case_001/artifacts/sample_2.fastq | 1670 | `0efbd0be0efb6516f9e3de411e9cff294301a70318aa7ddad0017a109a11f61d` |
| cases/case_001/expected.json | 232 | `def495e1ca3d9b997b7435fdad7cfc44b53f2f635fe7474c633db7b097990bbd` |
| cases/case_001/meta.json | 4116 | `33740e8da923b4f5fa3174c52c10340e600d588ad61cc2802e705dcfae03a7e3` |
| cases/case_001/task.md | 310 | `d029e16fa373c0a57c4c2a860288fb9cc63bd27dd0dc6dd0b110640327a313a4` |
| cases/case_002/artifacts/genome.fa.gz | 2053 | `90766201f1d6975388ea9e64b4c5e481b08c48e085f9573fcb70cfa2fef1914e` |
| cases/case_002/artifacts/integrity.json | 208 | `dd343825a2f24bc23a32398eacde8f164d15983946fd79cb1632b61008899081` |
| cases/case_002/expected.json | 192 | `1ee18be206b5593812bfd97018f0dc6654f15111e73db15fcc8361af59d4c976` |
| cases/case_002/meta.json | 2904 | `cc35ab19206b5f69836391180b28b53a61886c52be55e52676df4b2fe05a83a5` |
| cases/case_002/task.md | 284 | `f73b44c57aa98a734bd6b731f81425d7ea25b6b4bc78b6f98778250b66d9d3c8` |
| cases/case_003/artifacts/assembly.fa | 6087 | `cf4daba301c6b85736530dbe937c1ad7aae73aeb81dc769e1aa8ca2f096f27da` |
| cases/case_003/artifacts/layout.agp | 43 | `36a296d6f37f6ae0d018d3299eaa39cc1e5f7b259deef70258490b3191569a48` |
| cases/case_003/artifacts/lengths.json | 132 | `6fc096347310beef7e15ab41d2ae0f303ea69a19c6f157d150e9fd4d5b5addeb` |
| cases/case_003/expected.json | 180 | `0a82c209f82d7ea46dd4129c524e0ef248617de63c41d9df10054a9360d7178e` |
| cases/case_003/meta.json | 3301 | `a8006fe87394531105641d75407fdb9f6b285f1073b8bd44665eb17e631a6550` |
| cases/case_003/task.md | 349 | `a762e6508ec604b26ea12f9bd0ef8fca71fd55101f953c08095d2804ab253963` |
| cases/case_004/artifacts/mask_metrics.json | 131 | `1b4a16e852f3d42adacf7997d364ccd9ceca8e13d4647138adfba57357e33bea` |
| cases/case_004/artifacts/versions.json | 152 | `eab687016b75d2ed12448abfa90c069799cc9c260249e362f2332e48cb44e127` |
| cases/case_004/expected.json | 197 | `0f3cbe03c16d0543cfe616263ecc546113efc04ab783038fabacfe877456ddc9` |
| cases/case_004/meta.json | 3518 | `c06863639f32091435f526b0ba1a920fd3cf9fdb47f3949e65de3661e42101cd` |
| cases/case_004/task.md | 402 | `b3de5291955d9f0650d8edf85ef46bb0bc0346a77c81dcb20e0b9f6a6e755bd0` |
| cases/case_005/artifacts/mask_metrics.json | 139 | `b9f9f955ce6a3068b06a18a1be2d565e9b093dafec2f34604320dad270f7f736` |
| cases/case_005/artifacts/sequence.fa | 6088 | `f5e9cdcd009b82a34273a8cfcb73baa958d292e8f3e9787bd470a9358a406122` |
| cases/case_005/expected.json | 216 | `e6917d67cbea805b35b23cc264fd0851021012791ad6b7c7902c892ad47e55d2` |
| cases/case_005/meta.json | 2882 | `f5c30783ff24a5f8a93dc3514b2e51fab34c344a7b8ef98725d503569f17a3f8` |
| cases/case_005/task.md | 318 | `3600cf67c7e3d4e10aa12aa57e49830ce12a8229a7996fc63e48eb07b0c37f1a` |
| cases/case_006/artifacts/baseline.gtf | 854 | `8a8c95b4d0caf7392d0489fc46dc5cd630979a36371ffddd5d79bd554a92ecfe` |
| cases/case_006/artifacts/baseline_metrics.json | 243 | `20afaf22b7254bbbbc46f1fcc47e6aab67e0f22d34abaa8aa17f04d7648998f7` |
| cases/case_006/artifacts/delivery.gtf | 2733 | `f3e0a432b07106dd5f1f75ac37c370cd8231d418bbcfbb39bb3b9b2806befbc5` |
| cases/case_006/artifacts/delivery_metrics.json | 244 | `a37d80bd384b9119eaf6b1df58b021a8d4c04d114a72bc15dcc52931ee7e89b0` |
| cases/case_006/expected.json | 250 | `319cd69b3adb90ab22bfb264c9fb445b3772ef8146bd255fcd9e59e135fec78c` |
| cases/case_006/meta.json | 6776 | `62a960af8f52db4af4ccb629121ba5a2a68ca37aeef67c3dc5c2710f086a5570` |
| cases/case_006/task.md | 464 | `6cc2657f5c1da20188548a0d1f1d9dfca8723400abe3d5b3932ac4487e0f3ec0` |
| cases/case_007/artifacts/hints.gff | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| cases/case_007/artifacts/run_inputs.json | 99 | `82e8c24cc49c527f5c8097d0c73525ba4e7b3abfa145607723689641ba3221ea` |
| cases/case_007/expected.json | 227 | `65cc5729985ec7d531109f94a6715e71e9ad7117a852bb13e1ee4573fc2b417f` |
| cases/case_007/meta.json | 3694 | `8b2e98e37f1d9e4ee7d93b0674845bae8e5ab71824dcb10e562d3938e1332ac3` |
| cases/case_007/task.md | 313 | `334adab31cd392dd306a322142ae413bea210f5a11d2a8a80055731914151106` |
| cases/case_008/artifacts/models.gff3 | 2292 | `87e56b42db54fea750f1bb3552438629b812a6ff74158aaca0f2e5c85bef48c2` |
| cases/case_008/artifacts/reference.fa | 6088 | `8e60c02ea139876e147a31b2e697e8b109268099273a4b8fe35334aefdff2c83` |
| cases/case_008/artifacts/sequence_names.json | 148 | `6ac7a4e20b3aeeb3e819ae9306fc284b0f742588d7b06d4bf4d361c64263e700` |
| cases/case_008/expected.json | 216 | `2fbb1a1c0e496301b4a00e7570255dc8ec1cfa85286856ab302060ba0b3fc8e5` |
| cases/case_008/meta.json | 4278 | `1659333bd08d519e72b014d726a37d4ff3fd7316d38f8c6585780f29af883d0b` |
| cases/case_008/task.md | 361 | `87b3a0c6a24fa221315cf9e6eb5148b10f51a9234b8735432ada5900c7a42801` |
| cases/case_009/artifacts/annotation_statistics.json | 172 | `08e4aed75d71442a21e1ee414e801a15a84aeb50a2c52298a9edecf79a02abf3` |
| cases/case_009/artifacts/functional.tsv | 444 | `310daffcb8a9b1c3f5e0ea1429f4e7a0b6d686392b604fffe60340939063cca8` |
| cases/case_009/artifacts/query.faa | 6888 | `5cbc6512aa72b6f8767e28838a766a5d69f96921ef4c34726da18cd8a2b216cb` |
| cases/case_009/expected.json | 241 | `56dd9fcd5d96071f1d50df6ccaf2556a2c3e1ccd1b0214ef51bbda8772c39364` |
| cases/case_009/meta.json | 4297 | `f137953fe4cd3d571987e09fecb42c6562492d0493bdd9194091ab15d4c0d4ff` |
| cases/case_009/task.md | 453 | `d862a5ce25c922729dbcd3c3450bb8942f9dcf3896e301368f026dc94837865f` |
| cases/case_010/artifacts/annotation_statistics.json | 172 | `08e4aed75d71442a21e1ee414e801a15a84aeb50a2c52298a9edecf79a02abf3` |
| cases/case_010/artifacts/functional.tsv | 444 | `a8dc6d4af555793f205a9f66f8fc6f923fb4fd631b76fc8f399ea42ae604387f` |
| cases/case_010/artifacts/query.faa | 6888 | `5cbc6512aa72b6f8767e28838a766a5d69f96921ef4c34726da18cd8a2b216cb` |
| cases/case_010/expected.json | 222 | `88280ac458a9be9cda7f3a10d2f38ffb66b9af527fd20ea964f79011ff736db3` |
| cases/case_010/meta.json | 4381 | `149a83f2b64fe63d15b656c12ab5d7b52f9e3ba942ec7d5d246c2bcc7feac0a2` |
| cases/case_010/task.md | 453 | `d862a5ce25c922729dbcd3c3450bb8942f9dcf3896e301368f026dc94837865f` |
| cases/case_011/artifacts/mask_metrics.json | 131 | `1b4a16e852f3d42adacf7997d364ccd9ceca8e13d4647138adfba57357e33bea` |
| cases/case_011/artifacts/versions.json | 152 | `52a9bfd71c6a2901ab61c96b8a8b36aec638d01465e7b7d60e7a5d84e25b9a31` |
| cases/case_011/expected.json | 241 | `4b364c8339b88ad0dee1ce7013d083b00b980f009743c4d02abc6b434f18dd3e` |
| cases/case_011/meta.json | 3562 | `a83fbc5831958dd6cdcb4d79bdb3ebee71e8be9899a10e256dace57b310a71cb` |
| cases/case_011/task.md | 402 | `b3de5291955d9f0650d8edf85ef46bb0bc0346a77c81dcb20e0b9f6a6e755bd0` |
| cases/case_012/artifacts/annotation_metrics.json | 411 | `99da3ffe3ddf67b2ba5ec26b76e3e153ab12edfe11f94636305951ba4a6bc7e2` |
| cases/case_012/artifacts/models.gff3 | 3595 | `ac034f610e8150bf996252d0c0bea81e0952881b4e15637debd3defda0c27ddc` |
| cases/case_012/artifacts/proteins.faa | 398 | `bbaa68e624e7a9febb6c908ee352f75debcbca7425c0666af390ddae71b75db7` |
| cases/case_012/expected.json | 263 | `db03efc55d6ee6d24f0f85df8ec872faad5ff9d42a8e416e934b4a5f09bc6dfd` |
| cases/case_012/meta.json | 6645 | `2898d0bd0835f41e196a38f569d9fe2bbee180f211bb8589ece931cd4c022591` |
| cases/case_012/task.md | 345 | `917ab1a7892d16b57189e22cb0badf83751912dd9cb413cee7171b1395dbe18d` |
| cases/case_013/artifacts/annotation_metrics.json | 256 | `be4bb32d5774c8f62ecf29f553402421a6c28ac4fdbd13274fe5766dee8eca3e` |
| cases/case_013/artifacts/models.gff3 | 2573 | `15b8ae3b4287acacbc9f4dbec4ee020dd0f7828e4a82a96d74efa8fac9704e80` |
| cases/case_013/artifacts/proteins.faa | 860 | `ffacc231a1141f865bdd0ef60b348d35af73109bbf7d89fb8e6e6f2b0b722eea` |
| cases/case_013/expected.json | 274 | `11f10dd12e953947fc9a5732a6cf175249fd5a8c16c0236044edba175fc08704` |
| cases/case_013/meta.json | 4051 | `148f7f37412076cf470f8e1aca9b13ab7d9e3ed0fc7ee180dcd07d9c359fa972` |
| cases/case_013/task.md | 396 | `aa1529822f0233d86b91e6ffa86365aba234e47017adb43af96e63a823597778` |
| cases/case_014/artifacts/mask_metrics.json | 128 | `44160338b627d9ec1341e78faf6231a799d1620389c28e780feb2af67c4ac3c6` |
| cases/case_014/artifacts/versions.json | 152 | `52a9bfd71c6a2901ab61c96b8a8b36aec638d01465e7b7d60e7a5d84e25b9a31` |
| cases/case_014/expected.json | 253 | `e9f8d1b9f26a798fc4fed592ea1b9f42849f504f12cecf9ec2ab353d5a108a05` |
| cases/case_014/meta.json | 5440 | `2e06f8355df49e8532cdc6b1ae765e93a5ac644b4d04db872a4ac8519970eb01` |
| cases/case_014/task.md | 429 | `e91f1fd11ae092dfcdb0b1b5d0f6ea94c6185c65e87dbd9775df84ef8efe3862` |
| cases/case_015/artifacts/baseline.gtf | 854 | `8a8c95b4d0caf7392d0489fc46dc5cd630979a36371ffddd5d79bd554a92ecfe` |
| cases/case_015/artifacts/baseline_metrics.json | 243 | `20afaf22b7254bbbbc46f1fcc47e6aab67e0f22d34abaa8aa17f04d7648998f7` |
| cases/case_015/artifacts/delivery.gtf | 2733 | `f3e0a432b07106dd5f1f75ac37c370cd8231d418bbcfbb39bb3b9b2806befbc5` |
| cases/case_015/artifacts/delivery_metrics.json | 244 | `a37d80bd384b9119eaf6b1df58b021a8d4c04d114a72bc15dcc52931ee7e89b0` |
| cases/case_015/expected.json | 250 | `319cd69b3adb90ab22bfb264c9fb445b3772ef8146bd255fcd9e59e135fec78c` |
| cases/case_015/meta.json | 6783 | `48c28771933e3c9e4eb151ac500851904747f531aa7265ac3a8436eea52f0f1c` |
| cases/case_015/task.md | 544 | `2d1987172e024c6e28c6914040367c72b082676add5dfdf82745a6e6271d16be` |
| cases/case_016/artifacts/annotation_statistics.json | 172 | `08e4aed75d71442a21e1ee414e801a15a84aeb50a2c52298a9edecf79a02abf3` |
| cases/case_016/artifacts/functional.tsv | 444 | `310daffcb8a9b1c3f5e0ea1429f4e7a0b6d686392b604fffe60340939063cca8` |
| cases/case_016/artifacts/query.faa | 6888 | `5cbc6512aa72b6f8767e28838a766a5d69f96921ef4c34726da18cd8a2b216cb` |
| cases/case_016/expected.json | 241 | `8cf607d377e1ff4182d15dc5c1c6347b6414e55dd94e83d0c6b3d86f2f624b3e` |
| cases/case_016/meta.json | 4297 | `f0519cd849c0ef314383bc3f63fbeab05c6a16feaeac285d2647ea445ac2dd81` |
| cases/case_016/task.md | 533 | `8362b67eff3a958a4ae3b5af855a594e1f8e760facfaca8c241dfd75ea8e8ecb` |
| context/build_record.json | 25493 | `a345aa81dbd7baaa85d9c7a1036ab0f6d3754f545b53a51620722d087cd90712` |
| context/skill_context.md | 15919 | `c446bdbd8ad5d3f70932d28515e870f7bb547e33d10cdb1a0c9230884b9c9abf` |
| freeze.py | 8033 | `cff21dd9788547b2c38e643246eda469feb7237a40077c30a56b521954441e91` |
| inject/__init__.py | 73 | `9e90a39f43ef143bf21f36f9c8f568a9e34d95132fd398d17de17fa961c63da5` |
| inject/agp_layout.py | 944 | `389dcbe5770be5bb16237801a7dea2b4c02f9eda04114cd79b5f93da7cd5a7a8` |
| inject/common.py | 6557 | `097b77f8d706882b545d5c9e7dd748afde9cae11481faa30cfd8a3eff69c019a` |
| inject/functional_tables.py | 2816 | `8ea739c721ccce88ca0a46ad265e643a604e4b1b82033709b90bf2024922facb` |
| inject/gene_models.py | 1150 | `0d160db50e81e407428ee2f099dd48ce378b76286f9f82e4cc27d088b2bfb155` |
| inject/gzip_stream.py | 1139 | `869165550195c274cd9542a5ab7cdb896aead8f9845c7c25232a65f3d5c7e813` |
| inject/input_reads.py | 1003 | `ad9afa20373129eaabd399a5fd032ed4624d9946e175c88ce3c3938e266050cc` |
| inject/masking.py | 1037 | `d93e02f77a03feba8b1091dd39caa87cc736374e52a6c924a86a94614b14ce58` |
| inject/pressure.py | 243 | `e7f0fe105197315fb3d5bc6000b49ff5bdca41dd0fb3bd4781deafde816cca57` |
| inject/repeat_library.py | 811 | `fe005e6d57a6d644f8e2b98ee04df63a4d55ce2872d9f20bfab4e8e12149b3ad` |
| inject/rna_evidence.py | 800 | `a4eb227bcc7e52187f27073f4d16d071d810c524efe27a8f39dfc9e7bddc97b6` |
| inject/sequence_names.py | 1466 | `d4e1197894d75a6cae70a292847febcb80d1d389ccf6ce0919802ab0f67eb768` |
| preregistration.json | 795 | `20f841bc061f83d4d7ab57bc4c36cbfd3388b152404e3845fb584191478b79a4` |
| schemas/case_meta.schema.json | 20380 | `a4d9c0350769ccbc3093d2c22c6ee9a2fd22d37ca8041ee19ccf30046fd62ce1` |
| schemas/expected.schema.json | 2311 | `1bdc09028693774e0021cd1151ff1e02e8ded3afd958dbe192b237106c041f08` |
| schemas/model_output.schema.json | 2425 | `9d083ce3352b7d1ffe285b42b0b031f2e00b420a453847488a90932e78a8c9fb` |
| validate_cases.py | 11956 | `2337b4578eb462217c66099210d03dcb671224bd59871958f168c3b92a377817` |
| visible_input.py | 1953 | `ecefb375053fcbbf16d8dd7e610c98b8d81b2353e37f0e2e540694b6f5d58421` |

任何冻结内容变更须另起版本并记录 CHANGELOG；保留本版清单及结果。
