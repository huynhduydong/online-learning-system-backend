"""
Course validation schemas for request parameters and data validation.
Implements comprehensive validation for course catalog browsing functionality.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class SortOrder(str, Enum):
    """Valid sort orders for course catalog."""
    ASC = "asc"
    DESC = "desc"


class SortBy(str, Enum):
    """Valid sort fields for course catalog."""
    POPULARITY = "popularity"
    PRICE = "price"
    RATING = "rating"
    NEWEST = "newest"
    TITLE = "title"


class DifficultyLevel(str, Enum):
    """Valid difficulty levels for courses."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatus(str, Enum):
    """Valid course status values."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CourseCatalogRequest(BaseModel):
    """Validation schema for course catalog browsing requests."""
    
    # Pagination parameters
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)")
    per_page: int = Field(default=12, ge=1, le=50, description="Items per page (max 50)")
    
    # Filtering parameters
    category_id: Optional[int] = Field(default=None, ge=1, description="Filter by category ID")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price filter")
    difficulty: Optional[DifficultyLevel] = Field(default=None, description="Filter by difficulty level")
    min_rating: Optional[float] = Field(default=None, ge=1, le=5, description="Minimum rating filter")
    is_free: Optional[bool] = Field(default=None, description="Filter for free courses only")
    instructor_id: Optional[int] = Field(default=None, ge=1, description="Filter by instructor ID")
    
    # Sorting parameters
    sort_by: SortBy = Field(default=SortBy.POPULARITY, description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")
    
    # Search parameters
    search: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Search query")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        """Validate that max_price is greater than min_price if both are provided."""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v
    
    @validator('search')
    def validate_search_query(cls, v):
        """Validate search query format."""
        if v is not None:
            # Remove extra whitespace
            v = v.strip()
            if len(v) == 0:
                return None
            # Basic validation - no special characters that could cause issues
            if any(char in v for char in ['<', '>', '"', "'"]):
                raise ValueError('Search query contains invalid characters')
        return v


class CourseFilterRequest(BaseModel):
    """Validation schema for getting available filter options."""
    
    category_id: Optional[int] = Field(default=None, ge=1, description="Get filters for specific category")


class CourseSearchRequest(BaseModel):
    """Validation schema for course search requests."""
    
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=12, ge=1, le=50, description="Items per page")
    category_id: Optional[int] = Field(default=None, ge=1, description="Filter by category")
    
    @validator('query')
    def validate_search_query(cls, v):
        """Validate and clean search query."""
        v = v.strip()
        if len(v) == 0:
            raise ValueError('Search query cannot be empty')
        # Remove potentially harmful characters
        if any(char in v for char in ['<', '>', '"', "'"]):
            raise ValueError('Search query contains invalid characters')
        return v


class CourseCreateRequest(BaseModel):
    """Validation schema for course creation requests."""
    
    title: str = Field(..., min_length=5, max_length=200, description="Course title")
    short_description: str = Field(..., min_length=10, max_length=500, description="Short description")
    description: str = Field(..., min_length=50, max_length=5000, description="Full description")
    category_id: int = Field(..., ge=1, description="Category ID")
    price: float = Field(..., ge=0, description="Course price")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    duration_hours: int = Field(..., ge=1, le=1000, description="Course duration in hours")
    language: str = Field(default="vi", min_length=2, max_length=5, description="Course language")
    requirements: Optional[str] = Field(default=None, max_length=1000, description="Course requirements")
    what_you_will_learn: Optional[str] = Field(default=None, max_length=2000, description="Learning outcomes")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate course title."""
        v = v.strip()
        if len(v) < 5:
            raise ValueError('Title must be at least 5 characters long')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        """Validate course price."""
        if v < 0:
            raise ValueError('Price cannot be negative')
        # Round to 2 decimal places
        return round(v, 2)


class CourseUpdateRequest(BaseModel):
    """Validation schema for course update requests."""
    
    title: Optional[str] = Field(default=None, min_length=5, max_length=200)
    short_description: Optional[str] = Field(default=None, min_length=10, max_length=500)
    description: Optional[str] = Field(default=None, min_length=50, max_length=5000)
    category_id: Optional[int] = Field(default=None, ge=1)
    price: Optional[float] = Field(default=None, ge=0)
    difficulty: Optional[DifficultyLevel] = Field(default=None)
    duration_hours: Optional[int] = Field(default=None, ge=1, le=1000)
    language: Optional[str] = Field(default=None, min_length=2, max_length=5)
    requirements: Optional[str] = Field(default=None, max_length=1000)
    what_you_will_learn: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[CourseStatus] = Field(default=None)
    
    @validator('title')
    def validate_title(cls, v):
        """Validate course title if provided."""
        if v is not None:
            v = v.strip()
            if len(v) < 5:
                raise ValueError('Title must be at least 5 characters long')
        return v
    
    @validator('price')
    def validate_price(cls, v):
        """Validate course price if provided."""
        if v is not None:
            if v < 0:
                raise ValueError('Price cannot be negative')
            v = round(v, 2)
        return v


class CategoryCreateRequest(BaseModel):
    """Validation schema for category creation requests."""
    
    name: str = Field(..., min_length=2, max_length=100, description="Category name")
    description: Optional[str] = Field(default=None, max_length=500, description="Category description")
    parent_id: Optional[int] = Field(default=None, ge=1, description="Parent category ID")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate category name."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Category name must be at least 2 characters long')
        return v


class PaginationResponse(BaseModel):
    """Standard pagination response schema."""
    
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_prev: bool = Field(..., description="Has previous page")
    has_next: bool = Field(..., description="Has next page")
    prev_num: Optional[int] = Field(default=None, description="Previous page number")
    next_num: Optional[int] = Field(default=None, description="Next page number")


class CourseResponse(BaseModel):
    """Response schema for course data."""
    
    id: int
    title: str
    short_description: str
    slug: str
    price: float
    display_price: str
    difficulty: str
    duration_hours: int
    language: str
    average_rating: Optional[float]
    rating_count: int
    student_count: int
    instructor_name: str
    category_name: str
    thumbnail_url: Optional[str]
    created_at: str
    updated_at: str


class CourseCatalogResponse(BaseModel):
    """Response schema for course catalog with pagination."""
    
    courses: List[CourseResponse]
    pagination: PaginationResponse
    filters_applied: dict
    total_found: int