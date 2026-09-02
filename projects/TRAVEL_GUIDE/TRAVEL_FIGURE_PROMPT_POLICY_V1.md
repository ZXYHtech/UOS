# TRAVEL_GUIDE｜Route Figure Prompt Policy V1

Status: PROJECT_POLICY
Effective: 2026-09-02
SourceAdaptation: AI_BOOK FIGURE_PROMPT_PACKET_FORMAT_POLICY_V1 + BOOK_V1_FIGURE_PRODUCTION_POLICY_V2_4
RepositoryBoundary: standalone copy; no runtime dependency on AI_book

## Rules

1. One route-map generation task is delivered as one compact prompt packet beginning with: `分别生成X张独立图片，具体内容如下。每张图片必须独立生成、独立输出，不得拼图、宫格、分镜、contact sheet｜联系表或合成在同一画布中；各图片不得继承前一张的对象、构图和主题。FigureID仅用于任务映射，不得印在最终图片中。`
2. One FigureID maps to one complete, independently copyable subprompt and one independent image output. No `同上`, `继续上一张`, inherited layout, collage, storyboard or crop-to-split workflow.
3. Chinese is primary. Any necessary English technical term in the prompt must include Chinese translation, e.g. `Base Render｜基础渲染`, `Operational Schematic Map｜操作型示意路线图`.
4. Lock subject early: state what the image is and is not. For route maps, the subject is a phone-readable schematic travel route in a continuous Dujiangyan geography context; it is not a GIS/navigation screenshot, PPT/SaaS card, tourist poster, fantasy map or multi-panel dashboard.
5. Reference-driven: every route prompt must consume `MAP_FACT_SHEETS_V1.md` and `MAP_VALIDATION_POLICY.md`. The renderer may simplify scale but may not invent stations, gates, roads, bridges, attractions, restaurants, travel modes or route order.
6. Reader-clean: FigureID, TaskID, SourceID, AgentID, review metadata, source notes and workflow text must never appear in the image.
7. Base-render-first: because exact Chinese place names and entrance labels are operationally sensitive, the AI image stage is a no-readable-text `Base Render｜基础渲染`. No title, Chinese/English labels, numbers, percentages, station names, gate names, road names, legend text or readable signage. Use unlabeled visual node symbols, arrows, route-line styles and reserved blank callout space. Verified Chinese labels are added later in a separate vector/text overlay.
8. Visual grammar: distinguish rail, walking, optional local-car and optional/cut branches through clearly different line styles or icon classes without readable text. Keep a continuous map-like scene rather than card UI.
9. Evidence boundary: approximate visual scale is allowed; operational stop identity, sequence and connection type are authoritative. `Schematic scale ≠ navigation geometry｜示意比例不等于导航几何`.
10. No fabricated quantitative claims, rankings, scores, exact distances, exact walking minutes or crowd percentages unless explicitly supplied by the fact sheet.
11. Generic/no-brand: no logos, branded navigation UI, commercial SKU, advertising or sales-sheet styling.
12. Return QA order: FigureID mapping -> Subject QA -> route/order/spatial logic QA -> fact/evidence boundary QA -> text-clean QA -> visual/mobile QA. Wrong-subject or wrong-route output is REJECTED, never remapped opportunistically.
13. Prompt handoff does not mean image produced. After prompt delivery the route-map generation state is `AWAITING_RENDER_RETURN` until an actual image is returned and verified.
