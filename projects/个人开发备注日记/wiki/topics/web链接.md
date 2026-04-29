---
title: "Web链接"
type: topic
created: 2026-04-30
last_updated: 2026-04-30
source_count: 0
confidence: medium
status: active
tags: []
---

# 07 Web Urls

*6 notes grouped from Apple Notes*

---

## BASE  https   http   127 0 0 1 5555  

# BASE="https://http://127.0.0.1:5555/"

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p132 -->

<div>BASE=&quothttps://http://127.0.0.1:5555/&quot</div>
<div>curl -sS -X POST &quothttp://127.0.0.1:5555/oauth/token&quot \</div>
<div>  -H &quotContent-Type: application/x-www-form-urlencoded&quot \</div>
<div>  -d &quotgrant_type=client_credentials&quot \</div>
<div>  -d &quotclient_id=dsc-flow-extract&quot \</div>
<div>  -d &quotclient_secret=xrgPOrbF0Sn6JpVo45kO06pVEuzHVIks&quot</div>
<div><br></div>
<div><br></div>
<div>curl -sS -X POST &quothttp://127.0.0.1:5555/api/flow-extract/run&quot \</div>
<div>  -H &quotAuthorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ4TVhOOUVDUkxPYWFjUUc1VmNUTElpTTVxTTQwdzR6ZUtkUzJmTWVFMzZRIn0.eyJleHAiOjE3NzUzODkzMzAsImlhdCI6MTc3NTM4OTI3MCwianRpIjoidHJydGNjOmQwMjNiYTA1LWZiNGQtZmZmOC0xZDY0LTI2MWUyMzI3NzFkNSIsImlzcyI6Imh0dHA6Ly8xMjEuNC43OS4xMzg6ODA4MC9yZWFsbXMvbWFzdGVyIiwiYXVkIjpbImRzYy1mbG93LWV4dHJhY3QiLCJhY2NvdW50Il0sInN1YiI6IjBlM2NjMWYxLTg0Y2EtNDE3OS04Y2Y5LWU1ZDZhYjkxMDA0NyIsInR5cCI6IkJlYXJlciIsImF6cCI6ImRzYy1mbG93LWV4dHJhY3QiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIi8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLW1hc3RlciIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iLCJ1c2VyIiwicGxhdGZvcm0gYWRtaW4iLCJzdXBlciB1c2VyIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJlbWFpbCBwcm9maWxlIiwiY2xpZW50SG9zdCI6IjEzOS4yMjYuNi42MiIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoic2VydmljZS1hY2NvdW50LWRzYy1mbG93LWV4dHJhY3QiLCJjbGllbnRBZGRyZXNzIjoiMTM5LjIyNi42LjYyIiwiY2xpZW50X2lkIjoiZHNjLWZsb3ctZXh0cmFjdCJ9.kEDAw3hat3rIWkp7HLR8tAJE90YvMsJT_BOZwTA60MjrhJ7gz1NllG27w6_mpODGhzFu7XmXhjvu-zSiApR5TXnL4wgxGNoH6mszjQLkZ3wZ9glC9Sose-6ntErAzsVjJFWQ3yJRAI2ytr3TQ2apx52yyzUiYLZF--OgXj8jydExhIo2qK4rvPdBKwChyso1mKCxp7IvPbw0zK8OuyvMYN2g5ow1lBfgoVZhO0YCDLiS8i5Uu2usmtnmaesLZFuhd3sv5tbIibYl3Mhhtl2Txfcp2qS_IsF2YMwOq2St0xfutujz-KOwE94TWHywP7awPAs_biFQjr1-Hm2ejP8K9Q&quot \</div>
<div>  -H &quotContent-Type: application/json&quot \</div>
<div>  --data-binary @- &lt&lt'EOF'</div>
<div>{</div>
<div>  &quotschema_version&quot: &quotflow_extract_request_v2&quot,</div>
<div>  &quotlinks&quot: [</div>
<div>    {</div>
<div>      &quoturl&quot: &quothttp://localhost:5630/api/knowledge/407519c5-0bab-4c12-af6a-1ea0a8eb8286/download_file?dataset_id=407519c5-0bab-4c12-af6a-1ea0a8eb8286&ampfilename=%E5%AF%BF%E9%99%A9%E5%B9%B4%E7%BB%93SOP%E6%89%8B%E5%86%8C-ab03794d-5885-4184-9994-f412c0634285_merged.txt&quot,</div>
<div>      &quottitle&quot: &quot寿险年结SOP手册-ab03794d-5885-4184-9994-f412c0634285_merged.txt&quot,</div>
<div>      &quotasset_type&quot: &quottext&quot,</div>
<div>      &quotweak_ocr&quot: false,</div>
<div>      &quotblock_order&quot: 0</div>
<div>    }</div>
<div>  ]</div>
<div>}</div>
<div>EOF</div>

---

##    id    http   www southmoney com gupiao sjjh 202507 58608302 html 

# [{"id": "http://www.southmoney.com/gupiao/sjjh/202507/58608302.html…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p65 -->

<div><br></div>
<div><br></div>
<div><br></div>
<div>[{&quotid&quot: &quothttp://www.southmoney.com/gupiao/sjjh/202507/58608302.html&quot, &quottype&quot: &quoturl&quot, &quottitle&quot: &quotMiniMax上市公司十强:2025第一季度上市公司每股收益排行榜&quot, &quotsource&quot: &quothttp://www.southmoney.com/gupiao/sjjh/202507/58608302.html&quot, &quotcontext&quot: &quot[MiniMax上市公司十强:2025第一季度上市公司每股收益排行榜](http://www.southmoney.com/gupiao/sjjh/202507/58608302.html)&quot}, {&quotid&quot: &quothttps://www.sogou.com/web/link?url=hedJjaC291PvucEF_0E02dhidTBh4atIy1Ey8MyooaIuEtHm4cAf-ivOXM2Bv-ZPWacsUQ5cXj10WFvGQigA80fVaZ4p6WpVv87a6hSH7Oc.&quot, &quottype&quot: &quoturl&quot, &quottitle&quot: &quot2024年年报及2025年一季报业绩点评：创新与结构优化共振,业绩筑...&quot, &quotsource&quot: &quothttps://www.sogou.com/web/link?url=hedJjaC291PvucEF_0E02dhidTBh4atIy1Ey8MyooaIuEtHm4cAf-ivOXM2Bv-ZPWacsUQ5cXj10WFvGQigA80fVaZ4p6WpVv87a6hSH7Oc.&quot, &quotcontext&quot: &quot2025年4月20日-东方财富网研报中心：第一时间提供各大券商研究所报告，最大程度减少个人投资者与机构之间信息上的差异，使个人投资者更早的了解到上市公司基本面变化...&quot}, {&quotid&quot: &quothttps://www.sogou.com/web/link?url=hedJjaC291NDxZ6Wyr6RTsJ-pLcDi6NqmRFY0vcvbalv_UCV0NtSXsm_8c78MAX5gmdL88xgS_y8H3hzb6JqFQ..&quot, &quottype&quot: &quoturl&quot, &quottitle&quot: &quot2025年一季度国内生产总值初步核算结果_部门动态_中国政府网&quot, &quotsource&quot: &quothttps://www.sogou.com/web/link?url=hedJjaC291NDxZ6Wyr6RTsJ-pLcDi6NqmRFY0vcvbalv_UCV0NtSXsm_8c78MAX5gmdL88xgS_y8H3hzb6JqFQ..&quot, &quotcontext&quot: &quot2025年4月17日-我国2025年一季度GDP核算结果如下。 点击下载： 相关数据表 其他相关核... 本报告中的季度GDP数据是由国家统计局负责核算的全国数据，未包括香港...&quot}, {&quotid&quot: &quothttps://www.sogou.com/web/link?url=hedJjaC291O9i26gJQi5DCdQRoztLvNXrnilvTOuwmkdgjYEwUPd-TIhF00etQXTz98T-pCQ7Y8.&quot, &quottype&quot: &quoturl&quot, &quottitle&quot: &quotAMD公布2025一季度强劲的财务业绩,收入同比增长36%&quot, &quotsource&quot: &quothttps://www.sogou.com/web/link?url=hedJjaC291O9i26gJQi5DCdQRoztLvNXrnilvTOuwmkdgjYEwUPd-TIhF00etQXTz98T-pCQ7Y8.&quot, &quotcontext&quot: &quot2025年5月7日-AMD 公布了2025年第一季度强劲的财务业绩，收入达到 74 亿美元，同比增长 36%。该公司实现了 50% 的毛利率和 7.09 亿美元的净收入，相当于每股摊...&quot}]</div>

---

## curl --location --request POST  http   127 0 0 1 5555 api user login 

# curl --location --request POST 'http://127.0.0.1:5555/api/user/login…

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p127 -->

<div>curl --location --request POST 'http://127.0.0.1:5555/api/user/login' \</div>
<div>--header 'Content-Type: application/json' \</div>
<div>--header 'Authorization: {{apiKey}}' \</div>
<div>--data-raw '{</div>
<div>    &quotlogin_identifier&quot: &quotadmin&quot,</div>
<div>    &quotlogin_type&quot: &quotusername&quot,</div>
<div>    &quotpassword&quot: &quotAiwud3ujfe&quot</div>
<div>}'</div>

---

## curl -X POST  http   127 0 0 1 5630 knowledge image ocr   

# curl -X POST "http://127.0.0.1:5630/knowledge/image_ocr" \

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p72 -->

<div>curl -X POST &quothttp://127.0.0.1:5630/knowledge/image_ocr&quot \</div>
<div>  -F &quotfile=@/Users/aiassistant/Downloads/image.png&quot \</div>
<div>  -F &quotocr_language=ch&quot \</div>
<div>  -F &quotconfidence_interval=0.7&quot</div>

---

## http   127 0 0 1 5173 chat workspaceId 1 reuseArtifacts 1

# http://127.0.0.1:5173/chat?workspaceId=1&reuseArtifacts=1

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p143 -->

<div><b><h1>http://127.0.0.1:5173/chat?workspaceId=1&ampreuseArtifacts=1</h1></b><b><h1><br></h1></b></div>
<div><br></div>
<div><br></div>
<div>http://127.0.0.1:5173/chat?workspaceId=1&ampreuseArtifacts=1<br></div>
<div><br></div>
<div>http://127.0.0.1:5173/chat?workspaceId=1&ampreuseArtifacts=1<br></div>

---

## https   dashscope aliyuncs com compatible-mode v1

# https://dashscope.aliyuncs.com/compatible-mode/v1

<!-- Note ID: x-coredata://94F737D4-C461-4E87-B4CD-EEC2BFDEAA68/ICNote/p19 -->

<div>https://dashscope.aliyuncs.com/compatible-mode/v1<br></div>
<div><br></div>
<div>https://dashscope.aliyuncs.com/compatible-mode/v1</div>
<div><br></div>
<div><br></div>

---


