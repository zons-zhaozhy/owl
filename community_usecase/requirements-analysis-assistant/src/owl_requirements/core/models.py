from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Aspect(BaseModel):
    aspect: str
    score: int
    issues: List[str]
    recommendations: List[str]

class RequirementsQuality(BaseModel):
    score: int
    aspects: List[Aspect]

class AnalysisQuality(BaseModel):
    score: int
    aspects: List[Aspect]

class QualityScore(BaseModel):
    requirements_quality: RequirementsQuality
    analysis_quality: AnalysisQuality

class Issue(BaseModel):
    severity: str
    category: str
    description: str
    affected_items: List[str]
    recommendations: List[str]

class Recommendations(BaseModel):
    high_priority: List[str]
    medium_priority: List[str]
    low_priority: List[str]

class QualityReport(BaseModel):
    quality_score: QualityScore
    issues: List[Issue]
    recommendations: Recommendations 