"""学习模式服务 - 课程生成、知识分级、思维导图、进度追踪、个性化推荐"""
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    Material, LearningCourse, CourseKnowledgePoint, KnowledgeRelation,
    CourseStatus, KnowledgeTier, RelationType, Direction,
    KnowledgePoint, ParseTask, TaskStatus,
)
from app.services.qwen_service import qwen_service

logger = logging.getLogger(__name__)


class LearningModeService:
    """学习模式核心服务"""

    def _parse_json(self, text: str) -> dict | list | None:
        """解析AI返回的JSON，带容错处理"""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            logger.error("JSON解析失败，原始内容: %s", text[:500])
            return None

    def create_course(
        self,
        title: str,
        material_ids: list[int],
        db: Session,
        description: Optional[str] = None,
        direction_id: Optional[int] = None,
    ) -> LearningCourse:
        """创建学习课程"""
        # 验证资料存在性
        materials = db.query(Material).filter(Material.id.in_(material_ids)).all()
        found_ids = {m.id for m in materials}
        missing = set(material_ids) - found_ids
        if missing:
            raise ValueError(f"以下资料不存在: {missing}")

        if not materials:
            raise ValueError("至少需要选择一份资料")

        # 如果没有指定方向，尝试从第一份资料获取
        if direction_id is None and materials:
            direction_id = materials[0].direction_id

        course = LearningCourse(
            title=title,
            description=description,
            direction_id=direction_id,
            material_ids=material_ids,
            status=CourseStatus.PENDING,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    async def generate_course_content(self, course_id: int, db: Session) -> LearningCourse:
        """AI生成课程内容：分级知识点 + 关联关系 + 思维导图"""
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        # 设置状态为生成中
        course.status = CourseStatus.GENERATING
        db.commit()

        try:
            # 1. 收集资料内容
            materials_content = self._collect_materials_content(course.material_ids, db)
            if not materials_content:
                raise ValueError("所选资料内容为空")

            # 2. 清除旧数据（重新生成时）
            db.query(KnowledgeRelation).filter(KnowledgeRelation.course_id == course_id).delete()
            db.query(CourseKnowledgePoint).filter(CourseKnowledgePoint.course_id == course_id).delete()
            db.commit()

            # 3. AI提取分级知识点
            knowledge_points_data = await self._extract_tiered_knowledge(materials_content)

            # 4. 保存知识点
            name_to_point = self._save_knowledge_points(course_id, knowledge_points_data, db)

            # 5. AI分析知识关联
            if len(name_to_point) >= 2:
                relations_data = await self._analyze_knowledge_relations(knowledge_points_data)
                self._save_relations(course_id, relations_data, name_to_point, db)

            # 6. AI生成思维导图
            mindmap_md = await self._generate_mindmap_markdown(
                course.title, knowledge_points_data
            )
            course.mindmap_markdown = mindmap_md

            # 7. 更新课程统计
            course.total_points = len(name_to_point)
            course.mastered_points = 0
            course.progress_rate = 0
            course.status = CourseStatus.COMPLETED
            course.error_message = None
            db.commit()
            db.refresh(course)

        except Exception as e:
            logger.error("生成课程内容失败: %s", str(e), exc_info=True)
            course.status = CourseStatus.FAILED
            course.error_message = str(e)
            db.commit()
            raise

        return course

    def _collect_materials_content(self, material_ids: list[int], db: Session) -> str:
        """收集所有资料的内容（含key_points和知识解析数据）"""
        materials = db.query(Material).filter(Material.id.in_(material_ids)).all()
        parts = []

        for m in materials:
            section = f"## 资料：{m.title}\n\n"
            # 原始内容（截取前3000字避免prompt过长）
            content = m.content or ""
            if len(content) > 3000:
                content = content[:3000] + "...(内容过长已截断)"
            section += content + "\n\n"

            # 已有知识点
            if m.key_points:
                section += "### 已提取的知识点：\n"
                for kp in m.key_points:
                    if isinstance(kp, dict):
                        section += f"- {kp.get('point', '')}: {kp.get('description', '')}\n"
                section += "\n"

            parts.append(section)

        # 额外收集知识解析数据（ParseTask中的KnowledgePoint）
        parse_kps = (
            db.query(KnowledgePoint)
            .join(ParseTask)
            .filter(
                ParseTask.status == TaskStatus.COMPLETED,
                ParseTask.direction_id.in_(
                    db.query(Material.direction_id)
                    .filter(Material.id.in_(material_ids))
                    .distinct()
                ),
            )
            .all()
        )
        if parse_kps:
            section = "## 知识解析中的知识点：\n"
            for kp in parse_kps:
                section += f"- [{kp.category or '通用'}] {kp.name}: {kp.description}\n"
            parts.append(section)

        return "\n".join(parts)

    async def _extract_tiered_knowledge(self, materials_content: str) -> list[dict]:
        """AI提取分级知识点"""
        prompt = f"""你是一位专业的教学设计师。请分析以下学习资料，提取核心知识点并分为三个学习层级。

【学习资料】：
{materials_content}

【任务要求】：
1. 将知识点分为三个层级：
   - beginner（入门）：基础概念、术语定义、简单操作步骤
   - intermediate（进阶）：工作原理、实现流程、常见实践方法
   - advanced（高级）：优化技巧、架构设计、最佳实践、边界场景

2. 构建知识层次结构：
   - 每个知识点可以有父知识点（parent_name），用于构建树形结构
   - 没有父知识点的为顶层知识点，parent_name 设为 null

3. 为每个知识点提供：
   - name: 知识点名称（15字以内，不要重复）
   - description: 详细描述（100-200字）
   - tier: 层级（beginner/intermediate/advanced）
   - category: 分类标签（如"基础概念"、"实践技巧"、"架构设计"等）
   - importance: 重要程度（1-5，5最重要）
   - parent_name: 父知识点名称（顶层为null）
   - order_index: 在同层级中的学习顺序（从1开始）
   - estimated_minutes: 预估学习时长（分钟）

4. 总共提取 10-20 个知识点，beginner/intermediate/advanced 每级至少3个

【输出格式】：
严格返回 JSON 数组，不要其他内容：
[
  {{
    "name": "知识点名称",
    "description": "详细描述...",
    "tier": "beginner",
    "category": "基础概念",
    "importance": 5,
    "parent_name": null,
    "order_index": 1,
    "estimated_minutes": 30
  }}
]"""

        messages = [{"role": "user", "content": prompt}]
        result = await qwen_service._chat(messages, temperature=0.3, timeout=180.0)
        parsed = self._parse_json(result)

        if not parsed or not isinstance(parsed, list):
            logger.warning("知识点提取返回格式异常，使用默认结构")
            return [
                {
                    "name": "知识点提取失败",
                    "description": "AI未能正确提取知识点，请重试",
                    "tier": "beginner",
                    "category": "通用",
                    "importance": 3,
                    "parent_name": None,
                    "order_index": 1,
                    "estimated_minutes": 30,
                }
            ]
        return parsed

    def _save_knowledge_points(
        self,
        course_id: int,
        knowledge_points_data: list[dict],
        db: Session,
    ) -> dict[str, CourseKnowledgePoint]:
        """保存知识点并建立父子关系，返回 name -> point 映射"""
        name_to_point: dict[str, CourseKnowledgePoint] = {}

        # 第一轮：创建所有知识点（不设parent_id）
        for kp_data in knowledge_points_data:
            name = kp_data.get("name", "未命名")
            tier_str = kp_data.get("tier", "beginner")
            try:
                tier = KnowledgeTier(tier_str)
            except ValueError:
                tier = KnowledgeTier.BEGINNER

            point = CourseKnowledgePoint(
                course_id=course_id,
                name=name,
                description=kp_data.get("description", ""),
                tier=tier,
                category=kp_data.get("category"),
                importance=min(max(kp_data.get("importance", 3), 1), 5),
                order_index=kp_data.get("order_index", 0),
                estimated_minutes=kp_data.get("estimated_minutes", 30),
            )
            db.add(point)
            name_to_point[name] = point

        db.flush()

        # 第二轮：设置父子关系
        for kp_data in knowledge_points_data:
            name = kp_data.get("name", "未命名")
            parent_name = kp_data.get("parent_name")
            if parent_name and parent_name in name_to_point and name in name_to_point:
                name_to_point[name].parent_id = name_to_point[parent_name].id

        db.commit()
        return name_to_point

    async def _analyze_knowledge_relations(self, knowledge_points_data: list[dict]) -> list[dict]:
        """AI分析知识点关联关系"""
        kp_list_text = "\n".join(
            f"- {kp.get('name')}: {kp.get('description', '')[:80]}"
            for kp in knowledge_points_data
        )

        prompt = f"""你是一位学习路径规划专家。请分析以下知识点列表，识别它们之间的学习依赖和关联关系。

【知识点列表】：
{kp_list_text}

【关系类型】：
1. prerequisite（前置依赖）：必须先掌握A才能学习B
2. related（相关关联）：A和B属于相关概念，同时学习效果更好
3. extends（扩展关系）：B是A的深化或应用

【要求】：
- 只返回重要关系（强度>=50）
- 避免冗余（如A→B→C存在，不需要额外的A→C）
- 每个关系包含简短说明

【输出格式】：
严格返回 JSON 数组：
[
  {{
    "source_name": "知识点A",
    "target_name": "知识点B",
    "relation_type": "prerequisite",
    "strength": 85,
    "description": "理解A是掌握B的基础"
  }}
]"""

        messages = [{"role": "user", "content": prompt}]
        result = await qwen_service._chat(messages, temperature=0.3, timeout=120.0)
        parsed = self._parse_json(result)

        if not parsed or not isinstance(parsed, list):
            return []
        return parsed

    def _save_relations(
        self,
        course_id: int,
        relations_data: list[dict],
        name_to_point: dict[str, CourseKnowledgePoint],
        db: Session,
    ):
        """保存知识关联关系"""
        for rel_data in relations_data:
            source_name = rel_data.get("source_name", "")
            target_name = rel_data.get("target_name", "")
            source = name_to_point.get(source_name)
            target = name_to_point.get(target_name)

            if not source or not target or source.id == target.id:
                continue

            try:
                rel_type = RelationType(rel_data.get("relation_type", "related"))
            except ValueError:
                rel_type = RelationType.RELATED

            relation = KnowledgeRelation(
                course_id=course_id,
                source_point_id=source.id,
                target_point_id=target.id,
                relation_type=rel_type,
                strength=min(max(rel_data.get("strength", 50), 0), 100),
                description=rel_data.get("description", ""),
            )
            db.add(relation)

        db.commit()

    async def _generate_mindmap_markdown(
        self, course_title: str, knowledge_points_data: list[dict]
    ) -> str:
        """AI生成适用于markmap的思维导图Markdown"""
        kp_text = json.dumps(knowledge_points_data, ensure_ascii=False, indent=2)

        prompt = f"""你是一位知识可视化专家。请根据以下课程知识点，生成一份适用于 markmap 思维导图工具的 Markdown 文档。

【课程标题】：{course_title}

【知识点数据】：
{kp_text}

【要求】：
1. 使用标准 Markdown 标题层级结构
2. 第一级（#）为课程标题
3. 第二级（##）按知识层级分组：入门基础、进阶提升、高级精通
4. 第三级（###）为各分类
5. 使用列表项（-）列出具体知识点
6. 知识点名称后可用括号补充关键说明
7. 结构清晰，层次分明

【输出格式】：
直接返回 Markdown 文本，不要用代码块包裹：

# {course_title}

## 入门基础
### 分类名
- 知识点A（简要说明）
- 知识点B（简要说明）

## 进阶提升
### 分类名
- 知识点C（简要说明）

## 高级精通
### 分类名
- 知识点D（简要说明）"""

        messages = [{"role": "user", "content": prompt}]
        result = await qwen_service._chat(messages, temperature=0.5, timeout=120.0)

        # 清理可能的代码块包裹
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:])
            if result.endswith("```"):
                result = result[:-3].strip()
            elif "```" in result:
                result = result.split("```")[0].strip()

        return result

    def get_courses(self, db: Session) -> list[LearningCourse]:
        """获取课程列表"""
        return (
            db.query(LearningCourse)
            .order_by(LearningCourse.created_at.desc())
            .all()
        )

    def get_course_detail(self, course_id: int, db: Session) -> dict | None:
        """获取课程详情（含知识点和关联关系）"""
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if not course:
            return None

        # 获取知识点
        points = (
            db.query(CourseKnowledgePoint)
            .filter(CourseKnowledgePoint.course_id == course_id)
            .order_by(CourseKnowledgePoint.tier, CourseKnowledgePoint.order_index)
            .all()
        )

        # 计算 children_count
        point_children_count = {}
        for p in points:
            if p.parent_id:
                point_children_count[p.parent_id] = point_children_count.get(p.parent_id, 0) + 1

        points_response = []
        for p in points:
            points_response.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "tier": p.tier.value if hasattr(p.tier, 'value') else p.tier,
                "category": p.category,
                "importance": p.importance,
                "parent_id": p.parent_id,
                "order_index": p.order_index,
                "estimated_minutes": p.estimated_minutes,
                "mastery_level": float(p.mastery_level) if p.mastery_level else 0,
                "practice_count": p.practice_count,
                "correct_count": p.correct_count,
                "children_count": point_children_count.get(p.id, 0),
            })

        # 获取关联关系
        relations = (
            db.query(KnowledgeRelation)
            .filter(KnowledgeRelation.course_id == course_id)
            .all()
        )

        point_name_map = {p.id: p.name for p in points}
        relations_response = []
        for r in relations:
            relations_response.append({
                "id": r.id,
                "source_point_id": r.source_point_id,
                "source_point_name": point_name_map.get(r.source_point_id, ""),
                "target_point_id": r.target_point_id,
                "target_point_name": point_name_map.get(r.target_point_id, ""),
                "relation_type": r.relation_type.value if hasattr(r.relation_type, 'value') else r.relation_type,
                "strength": r.strength,
                "description": r.description,
            })

        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "direction_id": course.direction_id,
            "status": course.status.value if hasattr(course.status, 'value') else course.status,
            "total_points": course.total_points,
            "mastered_points": course.mastered_points,
            "progress_rate": float(course.progress_rate) if course.progress_rate else 0,
            "material_ids": course.material_ids or [],
            "material_count": len(course.material_ids) if course.material_ids else 0,
            "created_at": course.created_at,
            "updated_at": course.updated_at,
            "knowledge_points": points_response,
            "relations": relations_response,
        }

    def get_mindmap(self, course_id: int, db: Session) -> dict | None:
        """获取思维导图数据"""
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if not course:
            return None
        return {
            "course_id": course.id,
            "title": course.title,
            "mindmap_markdown": course.mindmap_markdown or "",
        }

    def get_learning_progress(self, course_id: int, db: Session) -> dict | None:
        """获取学习进度"""
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if not course:
            return None

        points = (
            db.query(CourseKnowledgePoint)
            .filter(CourseKnowledgePoint.course_id == course_id)
            .all()
        )

        mastery_threshold = 70
        weak_threshold = 60

        beginner_pts = [p for p in points if p.tier == KnowledgeTier.BEGINNER]
        intermediate_pts = [p for p in points if p.tier == KnowledgeTier.INTERMEDIATE]
        advanced_pts = [p for p in points if p.tier == KnowledgeTier.ADVANCED]

        def count_mastered(pts):
            return sum(1 for p in pts if float(p.mastery_level or 0) >= mastery_threshold)

        total_mastered = count_mastered(points)

        # 薄弱知识点
        weak_points = []
        for p in points:
            ml = float(p.mastery_level or 0)
            if ml < weak_threshold and p.practice_count > 0:
                weak_points.append({
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "tier": p.tier.value if hasattr(p.tier, 'value') else p.tier,
                    "category": p.category,
                    "importance": p.importance,
                    "parent_id": p.parent_id,
                    "order_index": p.order_index,
                    "estimated_minutes": p.estimated_minutes,
                    "mastery_level": ml,
                    "practice_count": p.practice_count,
                    "correct_count": p.correct_count,
                    "children_count": 0,
                })

        # 未掌握知识点的预估剩余时长
        remaining_minutes = sum(
            p.estimated_minutes
            for p in points
            if float(p.mastery_level or 0) < mastery_threshold
        )

        total = len(points)
        progress = (total_mastered / total * 100) if total > 0 else 0

        # 更新课程进度
        course.mastered_points = total_mastered
        course.progress_rate = progress
        db.commit()

        return {
            "course_id": course.id,
            "total_points": total,
            "mastered_points": total_mastered,
            "progress_rate": round(progress, 2),
            "beginner_total": len(beginner_pts),
            "beginner_mastered": count_mastered(beginner_pts),
            "intermediate_total": len(intermediate_pts),
            "intermediate_mastered": count_mastered(intermediate_pts),
            "advanced_total": len(advanced_pts),
            "advanced_mastered": count_mastered(advanced_pts),
            "weak_points": weak_points,
            "estimated_remaining_minutes": remaining_minutes,
        }

    async def get_recommendations(self, course_id: int, db: Session) -> dict:
        """获取个性化学习推荐"""
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if not course:
            raise ValueError("课程不存在")

        points = (
            db.query(CourseKnowledgePoint)
            .filter(CourseKnowledgePoint.course_id == course_id)
            .all()
        )

        if not points:
            return {"course_id": course_id, "recommendations": []}

        # 分类知识点
        mastered = [p for p in points if float(p.mastery_level or 0) >= 70]
        weak = [p for p in points if p.practice_count > 0 and float(p.mastery_level or 0) < 60]
        not_started = [p for p in points if p.practice_count == 0]

        # 如果全部掌握
        mastered_names = {p.name for p in mastered}
        if len(mastered) == len(points):
            return {"course_id": course_id, "recommendations": []}

        # 获取关联关系用于前置判断
        relations = (
            db.query(KnowledgeRelation)
            .filter(
                KnowledgeRelation.course_id == course_id,
                KnowledgeRelation.relation_type == RelationType.PREREQUISITE,
            )
            .all()
        )

        # 可学习的知识点（前置已掌握）
        point_name_map = {p.id: p.name for p in points}
        available = []
        for p in not_started + weak:
            # 检查所有前置依赖是否已掌握
            prerequisites = [r for r in relations if r.target_point_id == p.id]
            all_prereqs_met = all(
                point_name_map.get(r.source_point_id, "") in mastered_names
                for r in prerequisites
            )
            if all_prereqs_met or not prerequisites:
                available.append(p)

        if not available:
            # 没有满足前置条件的，推荐入门级
            available = [p for p in not_started if p.tier == KnowledgeTier.BEGINNER]
            if not available:
                available = not_started[:5] if not_started else weak[:5]

        # 调用AI推荐
        weak_text = ", ".join(p.name for p in weak[:10]) or "暂无"
        mastered_text = ", ".join(p.name for p in mastered[:10]) or "暂无"
        available_text = "\n".join(
            f"- {p.name} (层级: {p.tier.value if hasattr(p.tier, 'value') else p.tier}, 重要度: {p.importance})"
            for p in available[:15]
        )

        prompt = f"""你是一位个性化学习教练。根据学生的学习数据，推荐最适合当前学习的知识点。

【学生当前状态】：
- 薄弱知识点：{weak_text}
- 已掌握知识点：{mastered_text}
- 可学习知识点（前置条件已满足）：
{available_text}

【推荐标准】：
1. 优先推荐前置知识已掌握的知识点
2. 与薄弱点相关度高的优先
3. 重要程度高的优先
4. 符合循序渐进原则（先入门再进阶再高级）

请推荐 3-5 个最应该学习的知识点，按优先级排序。

【输出格式】：
严格返回 JSON 数组：
[
  {{
    "knowledge_point_name": "知识点名称",
    "reason": "推荐理由（50-100字）",
    "priority": 5,
    "related_weak_points": ["薄弱点A", "薄弱点B"]
  }}
]"""

        messages = [{"role": "user", "content": prompt}]
        result = await qwen_service._chat(messages, temperature=0.5, timeout=120.0)
        parsed = self._parse_json(result)

        recommendations = []
        point_id_map = {p.name: p for p in points}

        if parsed and isinstance(parsed, list):
            for rec in parsed:
                kp_name = rec.get("knowledge_point_name", "")
                point = point_id_map.get(kp_name)
                if point:
                    recommendations.append({
                        "knowledge_point_id": point.id,
                        "knowledge_point_name": kp_name,
                        "tier": point.tier.value if hasattr(point.tier, 'value') else point.tier,
                        "reason": rec.get("reason", ""),
                        "priority": rec.get("priority", 3),
                        "related_weak_points": rec.get("related_weak_points", []),
                    })

        # 如果AI推荐为空，用简单规则兜底
        if not recommendations and available:
            for p in available[:3]:
                recommendations.append({
                    "knowledge_point_id": p.id,
                    "knowledge_point_name": p.name,
                    "tier": p.tier.value if hasattr(p.tier, 'value') else p.tier,
                    "reason": f"建议学习此{'入门' if p.tier == KnowledgeTier.BEGINNER else '进阶' if p.tier == KnowledgeTier.INTERMEDIATE else '高级'}知识点",
                    "priority": p.importance,
                    "related_weak_points": [],
                })

        return {"course_id": course_id, "recommendations": recommendations}

    def delete_course(self, course_id: int, db: Session) -> bool:
        """删除课程（级联删除知识点和关联）"""
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if not course:
            return False
        db.delete(course)
        db.commit()
        return True

    def update_point_mastery(
        self, course_id: int, point_id: int, mastery_level: float, db: Session
    ) -> CourseKnowledgePoint | None:
        """更新知识点掌握度"""
        point = (
            db.query(CourseKnowledgePoint)
            .filter(
                CourseKnowledgePoint.id == point_id,
                CourseKnowledgePoint.course_id == course_id,
            )
            .first()
        )
        if not point:
            return None

        mastery_level = min(max(mastery_level, 0), 100)
        point.mastery_level = mastery_level
        point.practice_count += 1
        if mastery_level >= 70:
            point.correct_count += 1

        # 更新课程统计
        course = db.query(LearningCourse).filter(LearningCourse.id == course_id).first()
        if course:
            all_points = (
                db.query(CourseKnowledgePoint)
                .filter(CourseKnowledgePoint.course_id == course_id)
                .all()
            )
            mastered = sum(1 for p in all_points if float(p.mastery_level or 0) >= 70)
            total = len(all_points)
            course.mastered_points = mastered
            course.progress_rate = (mastered / total * 100) if total > 0 else 0

        db.commit()
        db.refresh(point)
        return point


# 单例
learning_mode_service = LearningModeService()
