from django import template

register = template.Library()


@register.filter
def get_initials(user):
    """Return 1-2 character initials from user's full name or username."""
    try:
        name = ''
        if hasattr(user, 'get_full_name') and user.get_full_name():
            name = user.get_full_name().strip()
        elif getattr(user, 'username', None):
            name = user.username.strip()
        if not name:
            return ''
        parts = name.split()
        if len(parts) == 1:
            # Use first two characters of single name
            return parts[0][:2].upper()
        # Take first letter of first and last name
        first = parts[0][0]
        last = parts[-1][0]
        return (first + last).upper()
    except Exception:
        return ''
