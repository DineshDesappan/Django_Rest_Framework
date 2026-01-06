"""
CUSTOM PERMISSIONS FOR IMDB CLONE REST API

This file defines custom permission classes that control who can perform which actions.

Permission Types:
1. IsAdminOrReadOnly: Anyone can view (GET), only admins can modify (POST/PUT/DELETE)
2. IsReviewUserOrReadOnly: Anyone can view, only review owner/admin can modify

Django permissions check: "Does this user have permission to do this action?"
"""

from rest_framework import permissions


# ==================== ADMIN OR READ-ONLY PERMISSION ====================
class IsAdminOrReadOnly(permissions.IsAdminUser):
    """
    Custom permission: Read access for everyone, Write access for admins only

    Inherits from: IsAdminUser (base permission that checks if user.is_staff = True)

    Permission Logic:
        - GET, HEAD, OPTIONS (SAFE_METHODS): Anyone can access ✅
        - POST, PUT, PATCH, DELETE: Only admin/staff users ❌

    Use Cases:
        - StreamPlatform API: Anyone can view platforms, only admins can add/edit/delete
        - Movie API (if enabled): Anyone can browse, only admins can manage

    Example Behavior:
        User Action                         | Regular User | Admin User
        ------------------------------------+--------------+------------
        GET /api/stream/                    | ✅ Allowed   | ✅ Allowed
        GET /api/stream/1/                  | ✅ Allowed   | ✅ Allowed
        POST /api/stream/ (create)          | ❌ Denied    | ✅ Allowed
        PUT /api/stream/1/ (update)         | ❌ Denied    | ✅ Allowed
        DELETE /api/stream/1/ (delete)      | ❌ Denied    | ✅ Allowed

    How it works:
        1. Check if request method is safe (GET, HEAD, OPTIONS)
        2. If safe → return True (allow everyone)
        3. If not safe (POST, PUT, DELETE) → check if user is staff/admin
        4. Return True only if user.is_staff = True
    """

    def has_permission(self, request, view):
        """
        Called before view is executed

        Args:
            request: The HTTP request object (contains method, user, etc.)
            view: The view being accessed

        Returns:
            True: Permission granted, proceed to view
            False: Permission denied, return 403 Forbidden
        """
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') - read-only operations
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow anyone to view/read
        else:
            # For write operations (POST, PUT, PATCH, DELETE)
            # Check if user exists AND user is staff/admin
            return bool(request.user and request.user.is_staff)


# ==================== REVIEW USER OR READ-ONLY PERMISSION ====================
class IsReviewUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Read access for everyone, Write access for review owner or admin

    Inherits from: BasePermission (base class for custom permissions)

    Permission Logic:
        - GET, HEAD, OPTIONS: Anyone can view reviews ✅
        - POST, PUT, PATCH, DELETE: Only review owner or admin ❌

    Use Cases:
        - Review API: Anyone can read reviews, only author/admin can edit/delete their review
        - Prevents users from editing other people's reviews

    Example Behavior:
        Scenario                            | Review Author | Other User | Admin
        ------------------------------------+---------------+------------+-------
        GET /api/movie/1/review/5/          | ✅ Allowed    | ✅ Allowed | ✅ Allowed
        PUT /api/movie/1/review/5/ (own)    | ✅ Allowed    | ❌ Denied  | ✅ Allowed
        DELETE /api/movie/1/review/5/ (own) | ✅ Allowed    | ❌ Denied  | ✅ Allowed
        PUT /api/movie/1/review/99/ (other) | ❌ Denied     | ❌ Denied  | ✅ Allowed

    How it works:
        1. Check if request method is safe (GET, HEAD, OPTIONS)
        2. If safe → return True (allow everyone to read)
        3. If not safe (PUT, DELETE) → check object ownership
        4. Compare review.review_user with request.user
        5. Return True if user is owner OR admin
    """

    def has_object_permission(self, request, view, obj):
        """
        Called after object is retrieved (for detail views)

        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The specific Review object being accessed

        Returns:
            True: Permission granted for this specific object
            False: Permission denied, return 403 Forbidden

        Note: This is called AFTER has_permission() passes
        """
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow anyone to view/read reviews
        else:
            # For write operations (PUT, PATCH, DELETE)
            # Allow if: user is the review author OR user is admin/staff
            # obj.review_user: The User who wrote this review
            # request.user: The User making the current request
            return obj.review_user == request.user or request.user.is_staff


"""
PERMISSION FLOW EXAMPLE:

Scenario: User tries to DELETE a review

Step 1: has_permission() is called
    - Checks general permission (is user authenticated?)
    - If fails → 401 Unauthorized or 403 Forbidden
    - If passes → proceed to step 2

Step 2: View retrieves the Review object from database

Step 3: has_object_permission() is called
    - Checks object-level permission (is user the owner?)
    - Compare obj.review_user with request.user
    - If user is owner or admin → return True → DELETE succeeds
    - If user is neither → return False → 403 Forbidden

REAL-WORLD EXAMPLE:

Database:
    Review #5: { "review_user": "john_doe", "movie": "Inception", "rating": 5 }

Request 1: john_doe tries to DELETE /api/movie/1/review/5/
    has_permission() → True (authenticated)
    has_object_permission() → True (obj.review_user == request.user)
    Result: ✅ Review deleted

Request 2: jane_smith tries to DELETE /api/movie/1/review/5/
    has_permission() → True (authenticated)
    has_object_permission() → False (obj.review_user != request.user, not admin)
    Result: ❌ 403 Forbidden "You do not have permission to perform this action"

Request 3: admin_user tries to DELETE /api/movie/1/review/5/
    has_permission() → True (authenticated)
    has_object_permission() → True (request.user.is_staff = True)
    Result: ✅ Review deleted (admin can delete any review)
"""
