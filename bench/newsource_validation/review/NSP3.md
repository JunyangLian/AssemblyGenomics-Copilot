# NSP3 完整配对审核材料

有答案的材料复核；不能作为盲审。两题均需独立读取原文。

# qc_003 逐记录材料复核

私有审核补充；不是盲审、真人专家审核或模型成绩。候选答案未改、未冻结。

## 每条 CDS → FAA 精确连接

| GFF 行 | protein_id | FAA header 行 | 精确连接 |
|---|---|---|---|
| 7 | NP_001096854.1 | 1 | True |
| 8 | NP_001096854.1 | 1 | True |
| 9 | NP_001096854.1 | 1 | True |
| 15 | NP_001245442.1 | 22 | True |
| 16 | NP_001245442.1 | 22 | True |
| 17 | NP_001245442.1 | 22 | True |
| 23 | NP_001245441.1 | 12 | True |
| 24 | NP_001245441.1 | 12 | True |
| 30 | NP_001284732.1 | 33 | True |
| 31 | NP_001284732.1 | 33 | True |
| 32 | NP_001284732.1 | 33 | True |
| 37 | NP_726658.1 | 48 | True |
| 38 | NP_726658.1 | 48 | True |
| 39 | NP_726658.1 | 48 | True |
| 43 | NP_569833.1 | 40 | True |
| 44 | NP_569833.1 | 40 | True |

## 全部直接 Parent 关系

| 子行/类型 | Parent | 父行/类型 | 子区间 | 父区间 | 序列相同 | 链相同 | 合同成立 |
|---|---|---|---|---|---|---|---|
| 3/mRNA | gene-Dmel_CG17636 | [2]/gene | [124370, 126714] | [124370, 126714] | True | True | True |
| 4/exon | rna-NM_001103384.3 | [3]/mRNA | [126626, 126714] | [124370, 126714] | True | True | True |
| 5/exon | rna-NM_001103384.3 | [3]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 6/exon | rna-NM_001103384.3 | [3]/mRNA | [124370, 125409] | [124370, 126714] | True | True | True |
| 7/CDS | rna-NM_001103384.3 | [3]/mRNA | [126715, 126719] | [124370, 126714] | True | True | False |
| 8/CDS | rna-NM_001103384.3 | [3]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 9/CDS | rna-NM_001103384.3 | [3]/mRNA | [124464, 125409] | [124370, 126714] | True | True | True |
| 10/mRNA | gene-Dmel_CG17636 | [2]/gene | [124370, 126714] | [124370, 126714] | True | True | True |
| 11/exon | rna-NM_001258513.2 | [10]/mRNA | [126626, 126714] | [124370, 126714] | True | True | True |
| 12/exon | rna-NM_001258513.2 | [10]/mRNA | [126363, 126496] | [124370, 126714] | True | True | True |
| 13/exon | rna-NM_001258513.2 | [10]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 14/exon | rna-NM_001258513.2 | [10]/mRNA | [124370, 125409] | [124370, 126714] | True | True | True |
| 15/CDS | rna-NM_001258513.2 | [10]/mRNA | [126363, 126409] | [124370, 126714] | True | True | True |
| 16/CDS | rna-NM_001258513.2 | [10]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 17/CDS | rna-NM_001258513.2 | [10]/mRNA | [124464, 125409] | [124370, 126714] | True | True | True |
| 18/mRNA | gene-Dmel_CG17636 | [2]/gene | [124370, 126714] | [124370, 126714] | True | True | True |
| 19/exon | rna-NM_001258512.2 | [18]/mRNA | [126626, 126714] | [124370, 126714] | True | True | True |
| 20/exon | rna-NM_001258512.2 | [18]/mRNA | [126355, 126496] | [124370, 126714] | True | True | True |
| 21/exon | rna-NM_001258512.2 | [18]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 22/exon | rna-NM_001258512.2 | [18]/mRNA | [124370, 125409] | [124370, 126714] | True | True | True |
| 23/CDS | rna-NM_001258512.2 | [18]/mRNA | [125495, 126054] | [124370, 126714] | True | True | True |
| 24/CDS | rna-NM_001258512.2 | [18]/mRNA | [124464, 125409] | [124370, 126714] | True | True | True |
| 26/mRNA | gene-Dmel_CG3038 | [25]/gene | [243954, 245856] | [243954, 245856] | True | True | True |
| 27/exon | rna-NM_001297803.1 | [26]/mRNA | [245412, 245856] | [243954, 245856] | True | True | True |
| 28/exon | rna-NM_001297803.1 | [26]/mRNA | [245097, 245346] | [243954, 245856] | True | True | True |
| 29/exon | rna-NM_001297803.1 | [26]/mRNA | [243954, 245009] | [243954, 245856] | True | True | True |
| 30/CDS | rna-NM_001297803.1 | [26]/mRNA | [245412, 245670] | [243954, 245856] | True | True | True |
| 31/CDS | rna-NM_001297803.1 | [26]/mRNA | [245097, 245346] | [243954, 245856] | True | True | True |
| 32/CDS | rna-NM_001297803.1 | [26]/mRNA | [244439, 245009] | [243954, 245856] | True | True | True |
| 33/mRNA | gene-Dmel_CG3038 | [25]/gene | [244061, 245856] | [243954, 245856] | True | True | True |
| 34/exon | rna-NM_166834.2 | [33]/mRNA | [245680, 245856] | [244061, 245856] | True | True | True |
| 35/exon | rna-NM_166834.2 | [33]/mRNA | [245412, 245578] | [244061, 245856] | True | True | True |
| 36/exon | rna-NM_166834.2 | [33]/mRNA | [244061, 245346] | [244061, 245856] | True | True | True |
| 37/CDS | rna-NM_166834.2 | [33]/mRNA | [245680, 245681] | [244061, 245856] | True | True | True |
| 38/CDS | rna-NM_166834.2 | [33]/mRNA | [245412, 245578] | [244061, 245856] | True | True | True |
| 39/CDS | rna-NM_166834.2 | [33]/mRNA | [244439, 245346] | [244061, 245856] | True | True | True |
| 40/mRNA | gene-Dmel_CG3038 | [25]/gene | [244061, 245856] | [243954, 245856] | True | True | True |
| 41/exon | rna-NM_130477.4 | [40]/mRNA | [245412, 245856] | [244061, 245856] | True | True | True |
| 42/exon | rna-NM_130477.4 | [40]/mRNA | [244061, 245346] | [244061, 245856] | True | True | True |
| 43/CDS | rna-NM_130477.4 | [40]/mRNA | [245412, 245670] | [244061, 245856] | True | True | True |
| 44/CDS | rna-NM_130477.4 | [40]/mRNA | [244439, 245346] | [244061, 245856] | True | True | True |

## 候选引用逐项定位

### E01

CDS 闭区间越过其 mRNA 父区间；长度不变也不能满足包含要求。

- artifacts/models.gff3:7

```text
NC_004354.4	RefSeq	CDS	126715	126719	.	-	0	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
```

- artifacts/models.gff3:3

```text
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001103384.3;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Name=NM_001103384.3;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
```

## 完整公开题目与候选答案

以下逐文件原文供复核。代码框行号与文件自身的行号不同，请以原始附件或上面的 pointer 为准。

### task.md

````text
# 下游输入审核

请审核Drosophila melanogaster的一组结构注释记录是否可以交给下游文件连接程序。输出统一规定的JSON。

本题审核输入文件，不是已完成的分析交付；没有提供可回退的旧版本。审核范围仅为给出的两套完整编码gene特征块及对应蛋白，不能外推全基因组注释质量。models.gff3是本次输入，proteins.faa是按ID查找序列的输入；record_counts.json仅列字面计数。

消费者读取GFF的Parent建立gene→mRNA→exon/CDS关系，并按每行CDS的protein_id精确查找FAA header第一个token。每个Parent必须在本题完整记录中存在且类型符合上述层级；子记录必须与父记录同seqid、同链，闭区间完全位于父记录内。FAA记录与不同protein_id对应的一组CDS一一相接。没有声明去版本号、改大小写、以Name或CDS ID代替protein_id等映射。

同一CDS的多片段可以重复ID，不能把CDS行数当蛋白条数。允许异构体和partial=true，不检查模型全长、翻译正确性或生物学功能；这些属性不豁免上述文件连接要求。除必要输入合同外，本题没有其它继续条件，也没有提供运行日志来解释上游过程。

请根据公开记录检查必要合同，并建议最小修复或补证。满足所有必要输入要求时可继续；必要连接或层级要求不能满足时，应先停止下游启动并修复。不要仅凭字面计数接近就认为可以继续。
````

### artifacts/models.gff3

````text
##gff-version 3
NC_004354.4	RefSeq	gene	124370	126714	.	-	.	ID=gene-Dmel_CG17636;Dbxref=FLYBASE:FBgn0025837,GeneID:5740847;Name=CG17636;cyt_map=1A1-1A1;gbkey=Gene;gen_map=1-0 cM;gene=CG17636;gene_biotype=protein_coding;gene_synonym=Dmel\CG17636,EG:23E12.1;locus_tag=Dmel_CG17636
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001103384.3;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Name=NM_001103384.3;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	exon	126626	126714	.	-	.	ID=exon-NM_001103384.3-1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	exon	125495	126259	.	-	.	ID=exon-NM_001103384.3-2;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	exon	124370	125409	.	-	.	ID=exon-NM_001103384.3-3;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	CDS	126715	126719	.	-	0	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
NC_004354.4	RefSeq	CDS	125495	126259	.	-	1	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001258513.2;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Name=NM_001258513.2;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	126626	126714	.	-	.	ID=exon-NM_001258513.2-1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	126363	126496	.	-	.	ID=exon-NM_001258513.2-2;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	125495	126259	.	-	.	ID=exon-NM_001258513.2-3;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	124370	125409	.	-	.	ID=exon-NM_001258513.2-4;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	CDS	126363	126409	.	-	0	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
NC_004354.4	RefSeq	CDS	125495	126259	.	-	1	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001258512.2;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Name=NM_001258512.2;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	126626	126714	.	-	.	ID=exon-NM_001258512.2-1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	126355	126496	.	-	.	ID=exon-NM_001258512.2-2;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	125495	126259	.	-	.	ID=exon-NM_001258512.2-3;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	124370	125409	.	-	.	ID=exon-NM_001258512.2-4;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	CDS	125495	126054	.	-	0	ID=cds-NP_001245441.1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBpp0297937,GeneID:5740847,GenBank:NP_001245441.1,FLYBASE:FBgn0025837;Name=NP_001245441.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_001245441.1
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001245441.1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBpp0297937,GeneID:5740847,GenBank:NP_001245441.1,FLYBASE:FBgn0025837;Name=NP_001245441.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_001245441.1
NC_004354.4	RefSeq	gene	243954	245856	.	-	.	ID=gene-Dmel_CG3038;Dbxref=FLYBASE:FBgn0040373,GeneID:30970;Name=CG3038;cyt_map=1A1-1A1;gbkey=Gene;gen_map=1-0 cM;gene=CG3038;gene_biotype=protein_coding;gene_synonym=dbeta3GnT,Dmel\CG3038,EG:BACR37P7.1,GalT3;locus_tag=Dmel_CG3038
NC_004354.4	RefSeq	mRNA	243954	245856	.	-	.	ID=rna-NM_001297803.1;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Name=NM_001297803.1;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	exon	245412	245856	.	-	.	ID=exon-NM_001297803.1-1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	exon	245097	245346	.	-	.	ID=exon-NM_001297803.1-2;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	exon	243954	245009	.	-	.	ID=exon-NM_001297803.1-3;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	CDS	245412	245670	.	-	0	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
NC_004354.4	RefSeq	CDS	245097	245346	.	-	2	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
NC_004354.4	RefSeq	CDS	244439	245009	.	-	1	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
NC_004354.4	RefSeq	mRNA	244061	245856	.	-	.	ID=rna-NM_166834.2;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Name=NM_166834.2;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	exon	245680	245856	.	-	.	ID=exon-NM_166834.2-1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	exon	245412	245578	.	-	.	ID=exon-NM_166834.2-2;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	exon	244061	245346	.	-	.	ID=exon-NM_166834.2-3;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	CDS	245680	245681	.	-	0	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
NC_004354.4	RefSeq	CDS	245412	245578	.	-	1	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
NC_004354.4	RefSeq	CDS	244439	245346	.	-	2	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
NC_004354.4	RefSeq	mRNA	244061	245856	.	-	.	ID=rna-NM_130477.4;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Name=NM_130477.4;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
NC_004354.4	RefSeq	exon	245412	245856	.	-	.	ID=exon-NM_130477.4-1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
NC_004354.4	RefSeq	exon	244061	245346	.	-	.	ID=exon-NM_130477.4-2;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
NC_004354.4	RefSeq	CDS	245412	245670	.	-	0	ID=cds-NP_569833.1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBpp0070103,GeneID:30970,GenBank:NP_569833.1,FLYBASE:FBgn0040373;Name=NP_569833.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_569833.1
NC_004354.4	RefSeq	CDS	244439	245346	.	-	2	ID=cds-NP_569833.1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBpp0070103,GeneID:30970,GenBank:NP_569833.1,FLYBASE:FBgn0040373;Name=NP_569833.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_569833.1
````

### artifacts/proteins.faa

````text
>NP_001096854.1 uncharacterized protein Dmel_CG17636, isoform A [Drosophila melanogaster]
MSCCKKYAVCWIILVVTALGVTLGLVFGLRSKAEEPRRIGAVASNGVGCAEVGGSILDIG
GSAADAAIATMLCEGVMLPHSLGVGGGFVATIYSRETEFSEVLIARETAPAAATQDMFVK
TEITGALSCAVPAEIYGYSELHDKYGRLPWKTLFQPTIDLCRRGILVSRYLSGVLQREEE
RIRNEPSMAEIFINPKTDEVYKQGEVMYRHTLAETLEIIADEGAKAIYGGGRVGRKLVED
IQAMGGIVTEEDLQSYNVRWEMPLHSHFSGGYKLITSTLPTSGAVLTFMLNVMEPLYTSN
TDKYWQRLIETFKHAYGHRTNLGDIHYEPDVQEMYENLIDPAFAAEIRKLILDDRTFEDM
SYYGANFANEEDHGTAHISVLAPNGDAISVTSTINSHLGAKVRSRQTGFILNDEMDDFST
PGKINAYGIPASPANFIKPGKRPMSSTCPSIVLDTHGNVKLIVGGAGGSKITTSVAQTIL
RYFVLHEPIEKAVNSGRLHHQLAPMHIDMEPNVPRHTVAYLSAIGHDIRFLEDDKAYSAQ
TAIGILGTEPHPVCDRRRVGSAVVVEPDRVE
>NP_001245441.1 uncharacterized protein Dmel_CG17636, isoform B [Drosophila melanogaster]
MLCEGVMLPHSLGVGGGFVATIYSRETEFSEVLIARETAPAAATQDMFVKTEITGALSCA
VPAEIYGYSELHDKYGRLPWKTLFQPTIDLCRRGILVSRYLSGVLQREEERIRNEPSMAE
IFINPKTDEVYKQGEVMYRHTLAETLEIIADEGAKAIYGGGRVGRKLVEDIQAMGGIVTE
EDLQSYNVRWEMPLHSHFSGGYKLITSTLPTSGAVLTFMLNVMEPLYTSNTDKYWQRLIE
TFKHAYGHRTNLGDIHYEPDVQEMYENLIDPAFAAEIRKLILDDRTFEDMSYYGANFANE
EDHGTAHISVLAPNGDAISVTSTINSHLGAKVRSRQTGFILNDEMDDFSTPGKINAYGIP
ASPANFIKPGKRPMSSTCPSIVLDTHGNVKLIVGGAGGSKITTSVAQTILRYFVLHEPIE
KAVNSGRLHHQLAPMHIDMEPNVPRHTVAYLSAIGHDIRFLEDDKAYSAQTAIGILGTEP
HPVCDRRRVGSAVVVEPDRVE
>NP_001245442.1 uncharacterized protein Dmel_CG17636, isoform C [Drosophila melanogaster]
MFYGELFDAFGDLLVGCCKKYAVCWIILVVTALGVTLGLVFGLRSKAEEPRRIGAVASNG
VGCAEVGGSILDIGGSAADAAIATMLCEGVMLPHSLGVGGGFVATIYSRETEFSEVLIAR
ETAPAAATQDMFVKTEITGALSCAVPAEIYGYSELHDKYGRLPWKTLFQPTIDLCRRGIL
VSRYLSGVLQREEERIRNEPSMAEIFINPKTDEVYKQGEVMYRHTLAETLEIIADEGAKA
IYGGGRVGRKLVEDIQAMGGIVTEEDLQSYNVRWEMPLHSHFSGGYKLITSTLPTSGAVL
TFMLNVMEPLYTSNTDKYWQRLIETFKHAYGHRTNLGDIHYEPDVQEMYENLIDPAFAAE
IRKLILDDRTFEDMSYYGANFANEEDHGTAHISVLAPNGDAISVTSTINSHLGAKVRSRQ
TGFILNDEMDDFSTPGKINAYGIPASPANFIKPGKRPMSSTCPSIVLDTHGNVKLIVGGA
GGSKITTSVAQTILRYFVLHEPIEKAVNSGRLHHQLAPMHIDMEPNVPRHTVAYLSAIGH
DIRFLEDDKAYSAQTAIGILGTEPHPVCDRRRVGSAVVVEPDRVE
>NP_001284732.1 uncharacterized protein Dmel_CG3038, isoform C [Drosophila melanogaster]
MRMRGRRLLPIILSLLLIVLLSLCYFSNHLRDSSQSRKNGFLLHLPLETKRNPSNPNTPL
SNLLNLTDFHYLLASNVCRKAKRELLAVLIVTSYAGHDALRSAHRQAIPQSKLEEMGLRR
VFLLAALPSREHFISQDQLASEQNRFGDLLQGNFIEDYRNLSYKHVMGLKYLETLEVREP
GLATSSTLLSGYVLDAKPPIRLRANKWYVSKKEYPQALYPAYLSGWLYVTNVPTAERIVA
EAERMSFFWIDDTWLTGVVRTRLGIPLERHNDWFSANAEFIDCCVRDLKKHNYECEYSVG
PNGGDDRLLVEFLHNVEKCYFDECVKRPVGKSLKETCLAAAKSRPPKHGFPEIKALRLR
>NP_569833.1 uncharacterized protein Dmel_CG3038, isoform A [Drosophila melanogaster]
MRMRGRRLLPIILSLLLIVLLSLCYFSNHLRDSSQSRKNGFLLHLPLETKRNPSNPNTPL
SNLLNLTDFHYLLASNVCRKAKRELLAVLIVTSYAGHDALRSAHRQAIPQSKLEEMGLRR
VFLLAALPSREHFISQDQLASEQNRFGDLLQGNFIEDYRNLSYKHVMGLKWVSEECKKQA
KFIIKLDDDIIYDVFHLRRYLETLEVREPGLATSSTLLSGYVLDAKPPIRLRANKWYVSK
KEYPQALYPAYLSGWLYVTNVPTAERIVAEAERMSFFWIDDTWLTGVVRTRLGIPLERHN
DWFSANAEFIDCCVRDLKKHNYECEYSVGPNGGDDRLLVEFLHNVEKCYFDECVKRPVGK
SLKETCLAAAKSRPPKHGFPEIKALRLR
>NP_726658.1 uncharacterized protein Dmel_CG3038, isoform B [Drosophila melanogaster]
MDSSQSRKNGFLLHLPLETKRNPSNPNTPLSNLLNLTDFHYLLASNVCRKAKRELLAVLI
VTSYAGHDALRSAHRQAIPQSKLEEMGLRRVFLLAALPSREHFISQDQLASEQNRFGDLL
QGNFIEDYRNLSYKHVMGLKWVSEECKKQAKFIIKLDDDIIYDVFHLRRYLETLEVREPG
LATSSTLLSGYVLDAKPPIRLRANKWYVSKKEYPQALYPAYLSGWLYVTNVPTAERIVAE
AERMSFFWIDDTWLTGVVRTRLGIPLERHNDWFSANAEFIDCCVRDLKKHNYECEYSVGP
NGGDDRLLVEFLHNVEKCYFDECVKRPVGKSLKETCLAAAKSRPPKHGFPEIKALRLR
````

### artifacts/record_counts.json

````text
{"cds_rows":16,"exon_rows":19,"gene_rows":2,"mrna_rows":6,"protein_records":6,"protein_residues":2762,"unique_cds_ids":6}
````

### expected.json

````text
{"acceptable_decisions":[{"observed_defect":"gff_hierarchy_inconsistent","root_cause":"gff_hierarchy_error","verdict":"block"}],"case_id":"qc_003","independent_review_status":"pending","key_evidence":[{"acceptable_pointers":["artifacts/models.gff3:7","artifacts/models.gff3:3"],"claim_id":"E01","required_for_joint":true,"review_note":"Author AI draft; not independent human review; pending user approval.","statement":"CDS 闭区间越过其 mRNA 父区间；长度不变也不能满足包含要求。","verification_method":"record_connection"}],"pair_id":"NSP3","rationale":"仅审核本题声明的文件连接与层级；不推断上游运行原因或生物学质量。","root_identifiability":"confirmed","schema_version":"newsource-case-1","user_approved":false}
````

### meta.json

````text
{"case_id":"qc_003","excerpt_policy":"固定规则选两个原始完整编码gene块和所有关联完整蛋白；仅格式重排LF/FAA60列，不代表完整基因组；确定性变体逐字段记录。","historical_rule_report_seen":true,"injection_script":"bench/newsource_validation/cases.py","mechanism_exposure":"seen_in_project_development","mechanism_family":"child_parent_interval","pair_id":"NSP3","pressure_parent":null,"review_status":"draft","schema_version":"newsource-case-1","seed":20261011,"source_exposure":"new_to_model_prompt_tool_development","source_files":[{"path":"sources/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz","selection":"{\"gene_ids\": [\"gene-Dmel_CG17636\", \"gene-Dmel_CG3038\"], \"policy\": {\"answer_status\": \"draft\", \"api_calls\": 0, \"artifact_read_pages_maximum\": 4, \"candidate_limit\": 50, \"candidate_limit_definition\": \"first 50 eligible blocks, not first 50 raw genes\", \"case_order\": \"sort SHA256(seed|accession|variant) then assign qc_NNN\", \"genes_selected\": 2, \"max_feature_rows_per_gene\": 40, \"max_visible_bytes\": 30000, \"normal_scope\": \"only declared closed connected coding subset\", \"page_bytes\": 16000, \"page_lines\": 200, \"require_multisegment_cds\": true, \"same_source_pairs\": true, \"seed\": 20261011, \"selection_order\": \"source GFF order; first two individually closed, connected eligible coding blocks within byte limit\"}, \"transform\": {\"after\": [\"126715\", \"126719\"], \"attribute\": \"CDS coordinates\", \"before\": [\"126626\", \"126630\"], \"policy\": \"one segment moved just beyond its own mRNA end, same segment length\"}}","sha256":"9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726","source_group":"GCF_000001215.4","source_origin":"/home/Lianjunyang/临时/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz"},{"path":"sources/GCF_000001215.4_Release_6_plus_ISO1_MT_protein.faa.gz","selection":"{\"gene_ids\": [\"gene-Dmel_CG17636\", \"gene-Dmel_CG3038\"], \"policy\": {\"answer_status\": \"draft\", \"api_calls\": 0, \"artifact_read_pages_maximum\": 4, \"candidate_limit\": 50, \"candidate_limit_definition\": \"first 50 eligible blocks, not first 50 raw genes\", \"case_order\": \"sort SHA256(seed|accession|variant) then assign qc_NNN\", \"genes_selected\": 2, \"max_feature_rows_per_gene\": 40, \"max_visible_bytes\": 30000, \"normal_scope\": \"only declared closed connected coding subset\", \"page_bytes\": 16000, \"page_lines\": 200, \"require_multisegment_cds\": true, \"same_source_pairs\": true, \"seed\": 20261011, \"selection_order\": \"source GFF order; first two individually closed, connected eligible coding blocks within byte limit\"}, \"transform\": {\"after\": [\"126715\", \"126719\"], \"attribute\": \"CDS coordinates\", \"before\": [\"126626\", \"126630\"], \"policy\": \"one segment moved just beyond its own mRNA end, same segment length\"}}","sha256":"4bf959b02c5b4c58accb36552e30bbf77f5088713b155ef4e02f4e6edc2d9dff","source_group":"GCF_000001215.4","source_origin":"/home/Lianjunyang/临时/GCF_000001215.4_Release_6_plus_ISO1_MT_protein.faa.gz"}],"source_group":"GCF_000001215.4","split":"sealed_test","stage":"structural_annotation","synthetic":true,"type":"fault","verbatim_tool_exceptions":[],"visible_contract":{"allowed_id_mapping":"exact only","artifact_roles":{"delivery":["artifacts/models.gff3","artifacts/proteins.faa","artifacts/record_counts.json"],"reference":[]},"consumer_contract":"完整Parent层级、同序列/链、闭区间包含、protein_id精确连接FAA首token","review_target":"input","scope":"declared_subset","usable_previous_result":false}}
````


# qc_012 逐记录材料复核

私有审核补充；不是盲审、真人专家审核或模型成绩。候选答案未改、未冻结。

## 每条 CDS → FAA 精确连接

| GFF 行 | protein_id | FAA header 行 | 精确连接 |
|---|---|---|---|
| 7 | NP_001096854.1 | 1 | True |
| 8 | NP_001096854.1 | 1 | True |
| 9 | NP_001096854.1 | 1 | True |
| 15 | NP_001245442.1 | 22 | True |
| 16 | NP_001245442.1 | 22 | True |
| 17 | NP_001245442.1 | 22 | True |
| 23 | NP_001245441.1 | 12 | True |
| 24 | NP_001245441.1 | 12 | True |
| 30 | NP_001284732.1 | 33 | True |
| 31 | NP_001284732.1 | 33 | True |
| 32 | NP_001284732.1 | 33 | True |
| 37 | NP_726658.1 | 48 | True |
| 38 | NP_726658.1 | 48 | True |
| 39 | NP_726658.1 | 48 | True |
| 43 | NP_569833.1 | 40 | True |
| 44 | NP_569833.1 | 40 | True |

## 全部直接 Parent 关系

| 子行/类型 | Parent | 父行/类型 | 子区间 | 父区间 | 序列相同 | 链相同 | 合同成立 |
|---|---|---|---|---|---|---|---|
| 3/mRNA | gene-Dmel_CG17636 | [2]/gene | [124370, 126714] | [124370, 126714] | True | True | True |
| 4/exon | rna-NM_001103384.3 | [3]/mRNA | [126626, 126714] | [124370, 126714] | True | True | True |
| 5/exon | rna-NM_001103384.3 | [3]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 6/exon | rna-NM_001103384.3 | [3]/mRNA | [124370, 125409] | [124370, 126714] | True | True | True |
| 7/CDS | rna-NM_001103384.3 | [3]/mRNA | [126626, 126630] | [124370, 126714] | True | True | True |
| 8/CDS | rna-NM_001103384.3 | [3]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 9/CDS | rna-NM_001103384.3 | [3]/mRNA | [124464, 125409] | [124370, 126714] | True | True | True |
| 10/mRNA | gene-Dmel_CG17636 | [2]/gene | [124370, 126714] | [124370, 126714] | True | True | True |
| 11/exon | rna-NM_001258513.2 | [10]/mRNA | [126626, 126714] | [124370, 126714] | True | True | True |
| 12/exon | rna-NM_001258513.2 | [10]/mRNA | [126363, 126496] | [124370, 126714] | True | True | True |
| 13/exon | rna-NM_001258513.2 | [10]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 14/exon | rna-NM_001258513.2 | [10]/mRNA | [124370, 125409] | [124370, 126714] | True | True | True |
| 15/CDS | rna-NM_001258513.2 | [10]/mRNA | [126363, 126409] | [124370, 126714] | True | True | True |
| 16/CDS | rna-NM_001258513.2 | [10]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 17/CDS | rna-NM_001258513.2 | [10]/mRNA | [124464, 125409] | [124370, 126714] | True | True | True |
| 18/mRNA | gene-Dmel_CG17636 | [2]/gene | [124370, 126714] | [124370, 126714] | True | True | True |
| 19/exon | rna-NM_001258512.2 | [18]/mRNA | [126626, 126714] | [124370, 126714] | True | True | True |
| 20/exon | rna-NM_001258512.2 | [18]/mRNA | [126355, 126496] | [124370, 126714] | True | True | True |
| 21/exon | rna-NM_001258512.2 | [18]/mRNA | [125495, 126259] | [124370, 126714] | True | True | True |
| 22/exon | rna-NM_001258512.2 | [18]/mRNA | [124370, 125409] | [124370, 126714] | True | True | True |
| 23/CDS | rna-NM_001258512.2 | [18]/mRNA | [125495, 126054] | [124370, 126714] | True | True | True |
| 24/CDS | rna-NM_001258512.2 | [18]/mRNA | [124464, 125409] | [124370, 126714] | True | True | True |
| 26/mRNA | gene-Dmel_CG3038 | [25]/gene | [243954, 245856] | [243954, 245856] | True | True | True |
| 27/exon | rna-NM_001297803.1 | [26]/mRNA | [245412, 245856] | [243954, 245856] | True | True | True |
| 28/exon | rna-NM_001297803.1 | [26]/mRNA | [245097, 245346] | [243954, 245856] | True | True | True |
| 29/exon | rna-NM_001297803.1 | [26]/mRNA | [243954, 245009] | [243954, 245856] | True | True | True |
| 30/CDS | rna-NM_001297803.1 | [26]/mRNA | [245412, 245670] | [243954, 245856] | True | True | True |
| 31/CDS | rna-NM_001297803.1 | [26]/mRNA | [245097, 245346] | [243954, 245856] | True | True | True |
| 32/CDS | rna-NM_001297803.1 | [26]/mRNA | [244439, 245009] | [243954, 245856] | True | True | True |
| 33/mRNA | gene-Dmel_CG3038 | [25]/gene | [244061, 245856] | [243954, 245856] | True | True | True |
| 34/exon | rna-NM_166834.2 | [33]/mRNA | [245680, 245856] | [244061, 245856] | True | True | True |
| 35/exon | rna-NM_166834.2 | [33]/mRNA | [245412, 245578] | [244061, 245856] | True | True | True |
| 36/exon | rna-NM_166834.2 | [33]/mRNA | [244061, 245346] | [244061, 245856] | True | True | True |
| 37/CDS | rna-NM_166834.2 | [33]/mRNA | [245680, 245681] | [244061, 245856] | True | True | True |
| 38/CDS | rna-NM_166834.2 | [33]/mRNA | [245412, 245578] | [244061, 245856] | True | True | True |
| 39/CDS | rna-NM_166834.2 | [33]/mRNA | [244439, 245346] | [244061, 245856] | True | True | True |
| 40/mRNA | gene-Dmel_CG3038 | [25]/gene | [244061, 245856] | [243954, 245856] | True | True | True |
| 41/exon | rna-NM_130477.4 | [40]/mRNA | [245412, 245856] | [244061, 245856] | True | True | True |
| 42/exon | rna-NM_130477.4 | [40]/mRNA | [244061, 245346] | [244061, 245856] | True | True | True |
| 43/CDS | rna-NM_130477.4 | [40]/mRNA | [245412, 245670] | [244061, 245856] | True | True | True |
| 44/CDS | rna-NM_130477.4 | [40]/mRNA | [244439, 245346] | [244061, 245856] | True | True | True |

## 候选引用逐项定位

### E01

每个不同 CDS protein_id 与完整 FAA 的首 token 精确接续；逐个 ID 验证，不以行数代替。

- artifacts/models.gff3:7

```text
NC_004354.4	RefSeq	CDS	126626	126630	.	-	0	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
```

- artifacts/models.gff3:8

```text
NC_004354.4	RefSeq	CDS	125495	126259	.	-	1	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
```

- artifacts/models.gff3:9

```text
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
```

- artifacts/models.gff3:15

```text
NC_004354.4	RefSeq	CDS	126363	126409	.	-	0	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
```

- artifacts/models.gff3:16

```text
NC_004354.4	RefSeq	CDS	125495	126259	.	-	1	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
```

- artifacts/models.gff3:17

```text
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
```

- artifacts/models.gff3:23

```text
NC_004354.4	RefSeq	CDS	125495	126054	.	-	0	ID=cds-NP_001245441.1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBpp0297937,GeneID:5740847,GenBank:NP_001245441.1,FLYBASE:FBgn0025837;Name=NP_001245441.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_001245441.1
```

- artifacts/models.gff3:24

```text
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001245441.1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBpp0297937,GeneID:5740847,GenBank:NP_001245441.1,FLYBASE:FBgn0025837;Name=NP_001245441.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_001245441.1
```

- artifacts/models.gff3:30

```text
NC_004354.4	RefSeq	CDS	245412	245670	.	-	0	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
```

- artifacts/models.gff3:31

```text
NC_004354.4	RefSeq	CDS	245097	245346	.	-	2	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
```

- artifacts/models.gff3:32

```text
NC_004354.4	RefSeq	CDS	244439	245009	.	-	1	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
```

- artifacts/models.gff3:37

```text
NC_004354.4	RefSeq	CDS	245680	245681	.	-	0	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
```

- artifacts/models.gff3:38

```text
NC_004354.4	RefSeq	CDS	245412	245578	.	-	1	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
```

- artifacts/models.gff3:39

```text
NC_004354.4	RefSeq	CDS	244439	245346	.	-	2	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
```

- artifacts/models.gff3:43

```text
NC_004354.4	RefSeq	CDS	245412	245670	.	-	0	ID=cds-NP_569833.1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBpp0070103,GeneID:30970,GenBank:NP_569833.1,FLYBASE:FBgn0040373;Name=NP_569833.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_569833.1
```

- artifacts/models.gff3:44

```text
NC_004354.4	RefSeq	CDS	244439	245346	.	-	2	ID=cds-NP_569833.1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBpp0070103,GeneID:30970,GenBank:NP_569833.1,FLYBASE:FBgn0040373;Name=NP_569833.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_569833.1
```

- artifacts/proteins.faa:1

```text
>NP_001096854.1 uncharacterized protein Dmel_CG17636, isoform A [Drosophila melanogaster]
```

- artifacts/proteins.faa:12

```text
>NP_001245441.1 uncharacterized protein Dmel_CG17636, isoform B [Drosophila melanogaster]
```

- artifacts/proteins.faa:22

```text
>NP_001245442.1 uncharacterized protein Dmel_CG17636, isoform C [Drosophila melanogaster]
```

- artifacts/proteins.faa:33

```text
>NP_001284732.1 uncharacterized protein Dmel_CG3038, isoform C [Drosophila melanogaster]
```

- artifacts/proteins.faa:40

```text
>NP_569833.1 uncharacterized protein Dmel_CG3038, isoform A [Drosophila melanogaster]
```

- artifacts/proteins.faa:48

```text
>NP_726658.1 uncharacterized protein Dmel_CG3038, isoform B [Drosophila melanogaster]
```

### E02

所有 Parent 接续且类型、序列/链与父子闭区间符合题面必要合同。

- artifacts/models.gff3:2

```text
NC_004354.4	RefSeq	gene	124370	126714	.	-	.	ID=gene-Dmel_CG17636;Dbxref=FLYBASE:FBgn0025837,GeneID:5740847;Name=CG17636;cyt_map=1A1-1A1;gbkey=Gene;gen_map=1-0 cM;gene=CG17636;gene_biotype=protein_coding;gene_synonym=Dmel\CG17636,EG:23E12.1;locus_tag=Dmel_CG17636
```

- artifacts/models.gff3:3

```text
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001103384.3;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Name=NM_001103384.3;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
```

- artifacts/models.gff3:10

```text
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001258513.2;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Name=NM_001258513.2;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
```

- artifacts/models.gff3:18

```text
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001258512.2;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Name=NM_001258512.2;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
```

- artifacts/models.gff3:25

```text
NC_004354.4	RefSeq	gene	243954	245856	.	-	.	ID=gene-Dmel_CG3038;Dbxref=FLYBASE:FBgn0040373,GeneID:30970;Name=CG3038;cyt_map=1A1-1A1;gbkey=Gene;gen_map=1-0 cM;gene=CG3038;gene_biotype=protein_coding;gene_synonym=dbeta3GnT,Dmel\CG3038,EG:BACR37P7.1,GalT3;locus_tag=Dmel_CG3038
```

- artifacts/models.gff3:26

```text
NC_004354.4	RefSeq	mRNA	243954	245856	.	-	.	ID=rna-NM_001297803.1;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Name=NM_001297803.1;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
```

- artifacts/models.gff3:33

```text
NC_004354.4	RefSeq	mRNA	244061	245856	.	-	.	ID=rna-NM_166834.2;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Name=NM_166834.2;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
```

- artifacts/models.gff3:40

```text
NC_004354.4	RefSeq	mRNA	244061	245856	.	-	.	ID=rna-NM_130477.4;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Name=NM_130477.4;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
```

原候选是代表性定位；完成全记录核对还需要以下行。此处补充材料，不修改 expected.json：

artifacts/models.gff3:4, artifacts/models.gff3:5, artifacts/models.gff3:6, artifacts/models.gff3:7, artifacts/models.gff3:8, artifacts/models.gff3:9, artifacts/models.gff3:11, artifacts/models.gff3:12, artifacts/models.gff3:13, artifacts/models.gff3:14, artifacts/models.gff3:15, artifacts/models.gff3:16, artifacts/models.gff3:17, artifacts/models.gff3:19, artifacts/models.gff3:20, artifacts/models.gff3:21, artifacts/models.gff3:22, artifacts/models.gff3:23, artifacts/models.gff3:24, artifacts/models.gff3:27, artifacts/models.gff3:28, artifacts/models.gff3:29, artifacts/models.gff3:30, artifacts/models.gff3:31, artifacts/models.gff3:32, artifacts/models.gff3:34, artifacts/models.gff3:35, artifacts/models.gff3:36, artifacts/models.gff3:37, artifacts/models.gff3:38, artifacts/models.gff3:39, artifacts/models.gff3:41, artifacts/models.gff3:42, artifacts/models.gff3:43, artifacts/models.gff3:44

## 完整公开题目与候选答案

以下逐文件原文供复核。代码框行号与文件自身的行号不同，请以原始附件或上面的 pointer 为准。

### task.md

````text
# 下游输入审核

请审核Drosophila melanogaster的一组结构注释记录是否可以交给下游文件连接程序。输出统一规定的JSON。

本题审核输入文件，不是已完成的分析交付；没有提供可回退的旧版本。审核范围仅为给出的两套完整编码gene特征块及对应蛋白，不能外推全基因组注释质量。models.gff3是本次输入，proteins.faa是按ID查找序列的输入；record_counts.json仅列字面计数。

消费者读取GFF的Parent建立gene→mRNA→exon/CDS关系，并按每行CDS的protein_id精确查找FAA header第一个token。每个Parent必须在本题完整记录中存在且类型符合上述层级；子记录必须与父记录同seqid、同链，闭区间完全位于父记录内。FAA记录与不同protein_id对应的一组CDS一一相接。没有声明去版本号、改大小写、以Name或CDS ID代替protein_id等映射。

同一CDS的多片段可以重复ID，不能把CDS行数当蛋白条数。允许异构体和partial=true，不检查模型全长、翻译正确性或生物学功能；这些属性不豁免上述文件连接要求。除必要输入合同外，本题没有其它继续条件，也没有提供运行日志来解释上游过程。

请根据公开记录检查必要合同，并建议最小修复或补证。满足所有必要输入要求时可继续；必要连接或层级要求不能满足时，应先停止下游启动并修复。不要仅凭字面计数接近就认为可以继续。
````

### artifacts/models.gff3

````text
##gff-version 3
NC_004354.4	RefSeq	gene	124370	126714	.	-	.	ID=gene-Dmel_CG17636;Dbxref=FLYBASE:FBgn0025837,GeneID:5740847;Name=CG17636;cyt_map=1A1-1A1;gbkey=Gene;gen_map=1-0 cM;gene=CG17636;gene_biotype=protein_coding;gene_synonym=Dmel\CG17636,EG:23E12.1;locus_tag=Dmel_CG17636
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001103384.3;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Name=NM_001103384.3;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	exon	126626	126714	.	-	.	ID=exon-NM_001103384.3-1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	exon	125495	126259	.	-	.	ID=exon-NM_001103384.3-2;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	exon	124370	125409	.	-	.	ID=exon-NM_001103384.3-3;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBtr0112921,GeneID:5740847,GenBank:NM_001103384.3,FLYBASE:FBgn0025837;Note=CG17636-RA%3B Dmel\CG17636-RA;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PA|gb|ABW09315;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_001103384.3
NC_004354.4	RefSeq	CDS	126626	126630	.	-	0	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
NC_004354.4	RefSeq	CDS	125495	126259	.	-	1	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001096854.1;Parent=rna-NM_001103384.3;Dbxref=FLYBASE:FBpp0111834,GeneID:5740847,GenBank:NP_001096854.1,FLYBASE:FBgn0025837;Name=NP_001096854.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_001096854.1
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001258513.2;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Name=NM_001258513.2;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	126626	126714	.	-	.	ID=exon-NM_001258513.2-1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	126363	126496	.	-	.	ID=exon-NM_001258513.2-2;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	125495	126259	.	-	.	ID=exon-NM_001258513.2-3;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	exon	124370	125409	.	-	.	ID=exon-NM_001258513.2-4;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBtr0307095,GeneID:5740847,GenBank:NM_001258513.2,FLYBASE:FBgn0025837;Note=CG17636-RC%3B Dmel\CG17636-RC;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PC|gb|AFH07158;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001258513.2
NC_004354.4	RefSeq	CDS	126363	126409	.	-	0	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
NC_004354.4	RefSeq	CDS	125495	126259	.	-	1	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001245442.1;Parent=rna-NM_001258513.2;Dbxref=FLYBASE:FBpp0297938,GeneID:5740847,GenBank:NP_001245442.1,FLYBASE:FBgn0025837;Name=NP_001245442.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001245442.1
NC_004354.4	RefSeq	mRNA	124370	126714	.	-	.	ID=rna-NM_001258512.2;Parent=gene-Dmel_CG17636;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Name=NM_001258512.2;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	126626	126714	.	-	.	ID=exon-NM_001258512.2-1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	126355	126496	.	-	.	ID=exon-NM_001258512.2-2;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	125495	126259	.	-	.	ID=exon-NM_001258512.2-3;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	exon	124370	125409	.	-	.	ID=exon-NM_001258512.2-4;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBtr0307094,GeneID:5740847,GenBank:NM_001258512.2,FLYBASE:FBgn0025837;Note=CG17636-RB%3B Dmel\CG17636-RB;gbkey=mRNA;gene=CG17636;locus_tag=Dmel_CG17636;orig_protein_id=gnl|FlyBase|CG17636-PB|gb|AFH07157;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_001258512.2
NC_004354.4	RefSeq	CDS	125495	126054	.	-	0	ID=cds-NP_001245441.1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBpp0297937,GeneID:5740847,GenBank:NP_001245441.1,FLYBASE:FBgn0025837;Name=NP_001245441.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_001245441.1
NC_004354.4	RefSeq	CDS	124464	125409	.	-	1	ID=cds-NP_001245441.1;Parent=rna-NM_001258512.2;Dbxref=FLYBASE:FBpp0297937,GeneID:5740847,GenBank:NP_001245441.1,FLYBASE:FBgn0025837;Name=NP_001245441.1;gbkey=CDS;gene=CG17636;locus_tag=Dmel_CG17636;orig_transcript_id=gnl|FlyBase|CG17636-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_001245441.1
NC_004354.4	RefSeq	gene	243954	245856	.	-	.	ID=gene-Dmel_CG3038;Dbxref=FLYBASE:FBgn0040373,GeneID:30970;Name=CG3038;cyt_map=1A1-1A1;gbkey=Gene;gen_map=1-0 cM;gene=CG3038;gene_biotype=protein_coding;gene_synonym=dbeta3GnT,Dmel\CG3038,EG:BACR37P7.1,GalT3;locus_tag=Dmel_CG3038
NC_004354.4	RefSeq	mRNA	243954	245856	.	-	.	ID=rna-NM_001297803.1;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Name=NM_001297803.1;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	exon	245412	245856	.	-	.	ID=exon-NM_001297803.1-1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	exon	245097	245346	.	-	.	ID=exon-NM_001297803.1-2;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	exon	243954	245009	.	-	.	ID=exon-NM_001297803.1-3;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBtr0340207,GeneID:30970,GenBank:NM_001297803.1,FLYBASE:FBgn0040373;Note=CG3038-RC%3B Dmel\CG3038-RC;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PC|gb|AHN59203;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C transcript variant C;transcript_id=NM_001297803.1
NC_004354.4	RefSeq	CDS	245412	245670	.	-	0	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
NC_004354.4	RefSeq	CDS	245097	245346	.	-	2	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
NC_004354.4	RefSeq	CDS	244439	245009	.	-	1	ID=cds-NP_001284732.1;Parent=rna-NM_001297803.1;Dbxref=FLYBASE:FBpp0309182,GeneID:30970,GenBank:NP_001284732.1,FLYBASE:FBgn0040373;Name=NP_001284732.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RC;product=uncharacterized protein%2C isoform C;protein_id=NP_001284732.1
NC_004354.4	RefSeq	mRNA	244061	245856	.	-	.	ID=rna-NM_166834.2;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Name=NM_166834.2;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	exon	245680	245856	.	-	.	ID=exon-NM_166834.2-1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	exon	245412	245578	.	-	.	ID=exon-NM_166834.2-2;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	exon	244061	245346	.	-	.	ID=exon-NM_166834.2-3;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBtr0070107,GeneID:30970,GenBank:NM_166834.2,FLYBASE:FBgn0040373;Note=CG3038-RB%3B Dmel\CG3038-RB;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PB|gb|AAN09009;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C transcript variant B;transcript_id=NM_166834.2
NC_004354.4	RefSeq	CDS	245680	245681	.	-	0	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
NC_004354.4	RefSeq	CDS	245412	245578	.	-	1	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
NC_004354.4	RefSeq	CDS	244439	245346	.	-	2	ID=cds-NP_726658.1;Parent=rna-NM_166834.2;Dbxref=FLYBASE:FBpp0070102,GeneID:30970,GenBank:NP_726658.1,FLYBASE:FBgn0040373;Name=NP_726658.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RB;product=uncharacterized protein%2C isoform B;protein_id=NP_726658.1
NC_004354.4	RefSeq	mRNA	244061	245856	.	-	.	ID=rna-NM_130477.4;Parent=gene-Dmel_CG3038;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Name=NM_130477.4;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
NC_004354.4	RefSeq	exon	245412	245856	.	-	.	ID=exon-NM_130477.4-1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
NC_004354.4	RefSeq	exon	244061	245346	.	-	.	ID=exon-NM_130477.4-2;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBtr0070108,GeneID:30970,GenBank:NM_130477.4,FLYBASE:FBgn0040373;Note=CG3038-RA%3B Dmel\CG3038-RA;gbkey=mRNA;gene=CG3038;locus_tag=Dmel_CG3038;orig_protein_id=gnl|FlyBase|CG3038-PA|gb|AAF45486;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C transcript variant A;transcript_id=NM_130477.4
NC_004354.4	RefSeq	CDS	245412	245670	.	-	0	ID=cds-NP_569833.1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBpp0070103,GeneID:30970,GenBank:NP_569833.1,FLYBASE:FBgn0040373;Name=NP_569833.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_569833.1
NC_004354.4	RefSeq	CDS	244439	245346	.	-	2	ID=cds-NP_569833.1;Parent=rna-NM_130477.4;Dbxref=FLYBASE:FBpp0070103,GeneID:30970,GenBank:NP_569833.1,FLYBASE:FBgn0040373;Name=NP_569833.1;gbkey=CDS;gene=CG3038;locus_tag=Dmel_CG3038;orig_transcript_id=gnl|FlyBase|CG3038-RA;product=uncharacterized protein%2C isoform A;protein_id=NP_569833.1
````

### artifacts/proteins.faa

````text
>NP_001096854.1 uncharacterized protein Dmel_CG17636, isoform A [Drosophila melanogaster]
MSCCKKYAVCWIILVVTALGVTLGLVFGLRSKAEEPRRIGAVASNGVGCAEVGGSILDIG
GSAADAAIATMLCEGVMLPHSLGVGGGFVATIYSRETEFSEVLIARETAPAAATQDMFVK
TEITGALSCAVPAEIYGYSELHDKYGRLPWKTLFQPTIDLCRRGILVSRYLSGVLQREEE
RIRNEPSMAEIFINPKTDEVYKQGEVMYRHTLAETLEIIADEGAKAIYGGGRVGRKLVED
IQAMGGIVTEEDLQSYNVRWEMPLHSHFSGGYKLITSTLPTSGAVLTFMLNVMEPLYTSN
TDKYWQRLIETFKHAYGHRTNLGDIHYEPDVQEMYENLIDPAFAAEIRKLILDDRTFEDM
SYYGANFANEEDHGTAHISVLAPNGDAISVTSTINSHLGAKVRSRQTGFILNDEMDDFST
PGKINAYGIPASPANFIKPGKRPMSSTCPSIVLDTHGNVKLIVGGAGGSKITTSVAQTIL
RYFVLHEPIEKAVNSGRLHHQLAPMHIDMEPNVPRHTVAYLSAIGHDIRFLEDDKAYSAQ
TAIGILGTEPHPVCDRRRVGSAVVVEPDRVE
>NP_001245441.1 uncharacterized protein Dmel_CG17636, isoform B [Drosophila melanogaster]
MLCEGVMLPHSLGVGGGFVATIYSRETEFSEVLIARETAPAAATQDMFVKTEITGALSCA
VPAEIYGYSELHDKYGRLPWKTLFQPTIDLCRRGILVSRYLSGVLQREEERIRNEPSMAE
IFINPKTDEVYKQGEVMYRHTLAETLEIIADEGAKAIYGGGRVGRKLVEDIQAMGGIVTE
EDLQSYNVRWEMPLHSHFSGGYKLITSTLPTSGAVLTFMLNVMEPLYTSNTDKYWQRLIE
TFKHAYGHRTNLGDIHYEPDVQEMYENLIDPAFAAEIRKLILDDRTFEDMSYYGANFANE
EDHGTAHISVLAPNGDAISVTSTINSHLGAKVRSRQTGFILNDEMDDFSTPGKINAYGIP
ASPANFIKPGKRPMSSTCPSIVLDTHGNVKLIVGGAGGSKITTSVAQTILRYFVLHEPIE
KAVNSGRLHHQLAPMHIDMEPNVPRHTVAYLSAIGHDIRFLEDDKAYSAQTAIGILGTEP
HPVCDRRRVGSAVVVEPDRVE
>NP_001245442.1 uncharacterized protein Dmel_CG17636, isoform C [Drosophila melanogaster]
MFYGELFDAFGDLLVGCCKKYAVCWIILVVTALGVTLGLVFGLRSKAEEPRRIGAVASNG
VGCAEVGGSILDIGGSAADAAIATMLCEGVMLPHSLGVGGGFVATIYSRETEFSEVLIAR
ETAPAAATQDMFVKTEITGALSCAVPAEIYGYSELHDKYGRLPWKTLFQPTIDLCRRGIL
VSRYLSGVLQREEERIRNEPSMAEIFINPKTDEVYKQGEVMYRHTLAETLEIIADEGAKA
IYGGGRVGRKLVEDIQAMGGIVTEEDLQSYNVRWEMPLHSHFSGGYKLITSTLPTSGAVL
TFMLNVMEPLYTSNTDKYWQRLIETFKHAYGHRTNLGDIHYEPDVQEMYENLIDPAFAAE
IRKLILDDRTFEDMSYYGANFANEEDHGTAHISVLAPNGDAISVTSTINSHLGAKVRSRQ
TGFILNDEMDDFSTPGKINAYGIPASPANFIKPGKRPMSSTCPSIVLDTHGNVKLIVGGA
GGSKITTSVAQTILRYFVLHEPIEKAVNSGRLHHQLAPMHIDMEPNVPRHTVAYLSAIGH
DIRFLEDDKAYSAQTAIGILGTEPHPVCDRRRVGSAVVVEPDRVE
>NP_001284732.1 uncharacterized protein Dmel_CG3038, isoform C [Drosophila melanogaster]
MRMRGRRLLPIILSLLLIVLLSLCYFSNHLRDSSQSRKNGFLLHLPLETKRNPSNPNTPL
SNLLNLTDFHYLLASNVCRKAKRELLAVLIVTSYAGHDALRSAHRQAIPQSKLEEMGLRR
VFLLAALPSREHFISQDQLASEQNRFGDLLQGNFIEDYRNLSYKHVMGLKYLETLEVREP
GLATSSTLLSGYVLDAKPPIRLRANKWYVSKKEYPQALYPAYLSGWLYVTNVPTAERIVA
EAERMSFFWIDDTWLTGVVRTRLGIPLERHNDWFSANAEFIDCCVRDLKKHNYECEYSVG
PNGGDDRLLVEFLHNVEKCYFDECVKRPVGKSLKETCLAAAKSRPPKHGFPEIKALRLR
>NP_569833.1 uncharacterized protein Dmel_CG3038, isoform A [Drosophila melanogaster]
MRMRGRRLLPIILSLLLIVLLSLCYFSNHLRDSSQSRKNGFLLHLPLETKRNPSNPNTPL
SNLLNLTDFHYLLASNVCRKAKRELLAVLIVTSYAGHDALRSAHRQAIPQSKLEEMGLRR
VFLLAALPSREHFISQDQLASEQNRFGDLLQGNFIEDYRNLSYKHVMGLKWVSEECKKQA
KFIIKLDDDIIYDVFHLRRYLETLEVREPGLATSSTLLSGYVLDAKPPIRLRANKWYVSK
KEYPQALYPAYLSGWLYVTNVPTAERIVAEAERMSFFWIDDTWLTGVVRTRLGIPLERHN
DWFSANAEFIDCCVRDLKKHNYECEYSVGPNGGDDRLLVEFLHNVEKCYFDECVKRPVGK
SLKETCLAAAKSRPPKHGFPEIKALRLR
>NP_726658.1 uncharacterized protein Dmel_CG3038, isoform B [Drosophila melanogaster]
MDSSQSRKNGFLLHLPLETKRNPSNPNTPLSNLLNLTDFHYLLASNVCRKAKRELLAVLI
VTSYAGHDALRSAHRQAIPQSKLEEMGLRRVFLLAALPSREHFISQDQLASEQNRFGDLL
QGNFIEDYRNLSYKHVMGLKWVSEECKKQAKFIIKLDDDIIYDVFHLRRYLETLEVREPG
LATSSTLLSGYVLDAKPPIRLRANKWYVSKKEYPQALYPAYLSGWLYVTNVPTAERIVAE
AERMSFFWIDDTWLTGVVRTRLGIPLERHNDWFSANAEFIDCCVRDLKKHNYECEYSVGP
NGGDDRLLVEFLHNVEKCYFDECVKRPVGKSLKETCLAAAKSRPPKHGFPEIKALRLR
````

### artifacts/record_counts.json

````text
{"cds_rows":16,"exon_rows":19,"gene_rows":2,"mrna_rows":6,"protein_records":6,"protein_residues":2762,"unique_cds_ids":6}
````

### expected.json

````text
{"acceptable_decisions":[{"observed_defect":"none","root_cause":"none","verdict":"pass"}],"case_id":"qc_012","independent_review_status":"pending","key_evidence":[{"acceptable_pointers":["artifacts/models.gff3:7","artifacts/models.gff3:8","artifacts/models.gff3:9","artifacts/models.gff3:15","artifacts/models.gff3:16","artifacts/models.gff3:17","artifacts/models.gff3:23","artifacts/models.gff3:24","artifacts/models.gff3:30","artifacts/models.gff3:31","artifacts/models.gff3:32","artifacts/models.gff3:37","artifacts/models.gff3:38","artifacts/models.gff3:39","artifacts/models.gff3:43","artifacts/models.gff3:44","artifacts/proteins.faa:1","artifacts/proteins.faa:12","artifacts/proteins.faa:22","artifacts/proteins.faa:33","artifacts/proteins.faa:40","artifacts/proteins.faa:48"],"claim_id":"E01","required_for_joint":true,"review_note":"Author AI draft; not independent human review; pending user approval.","statement":"每个不同 CDS protein_id 与完整 FAA 的首 token 精确接续；逐个 ID 验证，不以行数代替。","verification_method":"record_connection"},{"acceptable_pointers":["artifacts/models.gff3:2","artifacts/models.gff3:3","artifacts/models.gff3:10","artifacts/models.gff3:18","artifacts/models.gff3:25","artifacts/models.gff3:26","artifacts/models.gff3:33","artifacts/models.gff3:40"],"claim_id":"E02","required_for_joint":true,"review_note":"Author AI draft; not independent human review; pending user approval.","statement":"所有 Parent 接续且类型、序列/链与父子闭区间符合题面必要合同。","verification_method":"record_connection"}],"pair_id":"NSP3","rationale":"仅审核本题声明的文件连接与层级；不推断上游运行原因或生物学质量。","root_identifiability":"no_defect","schema_version":"newsource-case-1","user_approved":false}
````

### meta.json

````text
{"case_id":"qc_012","excerpt_policy":"固定规则选两个原始完整编码gene块和所有关联完整蛋白；仅格式重排LF/FAA60列，不代表完整基因组；确定性变体逐字段记录。","historical_rule_report_seen":true,"injection_script":"bench/newsource_validation/cases.py","mechanism_exposure":"seen_in_project_development","mechanism_family":"child_parent_interval","pair_id":"NSP3","pressure_parent":null,"review_status":"draft","schema_version":"newsource-case-1","seed":20261011,"source_exposure":"new_to_model_prompt_tool_development","source_files":[{"path":"sources/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz","selection":"{\"gene_ids\": [\"gene-Dmel_CG17636\", \"gene-Dmel_CG3038\"], \"policy\": {\"answer_status\": \"draft\", \"api_calls\": 0, \"artifact_read_pages_maximum\": 4, \"candidate_limit\": 50, \"candidate_limit_definition\": \"first 50 eligible blocks, not first 50 raw genes\", \"case_order\": \"sort SHA256(seed|accession|variant) then assign qc_NNN\", \"genes_selected\": 2, \"max_feature_rows_per_gene\": 40, \"max_visible_bytes\": 30000, \"normal_scope\": \"only declared closed connected coding subset\", \"page_bytes\": 16000, \"page_lines\": 200, \"require_multisegment_cds\": true, \"same_source_pairs\": true, \"seed\": 20261011, \"selection_order\": \"source GFF order; first two individually closed, connected eligible coding blocks within byte limit\"}, \"transform\": \"unmodified source subset\"}","sha256":"9a372f10f86f4fe4222d070a101716b7565affdd6cb96efae249e8afa3b2c726","source_group":"GCF_000001215.4","source_origin":"/home/Lianjunyang/临时/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.gff.gz"},{"path":"sources/GCF_000001215.4_Release_6_plus_ISO1_MT_protein.faa.gz","selection":"{\"gene_ids\": [\"gene-Dmel_CG17636\", \"gene-Dmel_CG3038\"], \"policy\": {\"answer_status\": \"draft\", \"api_calls\": 0, \"artifact_read_pages_maximum\": 4, \"candidate_limit\": 50, \"candidate_limit_definition\": \"first 50 eligible blocks, not first 50 raw genes\", \"case_order\": \"sort SHA256(seed|accession|variant) then assign qc_NNN\", \"genes_selected\": 2, \"max_feature_rows_per_gene\": 40, \"max_visible_bytes\": 30000, \"normal_scope\": \"only declared closed connected coding subset\", \"page_bytes\": 16000, \"page_lines\": 200, \"require_multisegment_cds\": true, \"same_source_pairs\": true, \"seed\": 20261011, \"selection_order\": \"source GFF order; first two individually closed, connected eligible coding blocks within byte limit\"}, \"transform\": \"unmodified source subset\"}","sha256":"4bf959b02c5b4c58accb36552e30bbf77f5088713b155ef4e02f4e6edc2d9dff","source_group":"GCF_000001215.4","source_origin":"/home/Lianjunyang/临时/GCF_000001215.4_Release_6_plus_ISO1_MT_protein.faa.gz"}],"source_group":"GCF_000001215.4","split":"sealed_test","stage":"structural_annotation","synthetic":true,"type":"normal","verbatim_tool_exceptions":[],"visible_contract":{"allowed_id_mapping":"exact only","artifact_roles":{"delivery":["artifacts/models.gff3","artifacts/proteins.faa","artifacts/record_counts.json"],"reference":[]},"consumer_contract":"完整Parent层级、同序列/链、闭区间包含、protein_id精确连接FAA首token","review_target":"input","scope":"declared_subset","usable_previous_result":false}}
````
