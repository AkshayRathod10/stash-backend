from django.core.cache import cache
import functools, hashlib, json

def cache_result(ttl=300, vary_on_user=False):
    """Decorator: cache view or service method results in Redis."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key_data = f'{fn.__module__}.{fn.__qualname__}:{args}:{kwargs}'
            if vary_on_user and hasattr(args[0], 'request'):
                key_data += f':user={args[0].request.user.pk}'
            key = hashlib.md5(key_data.encode()).hexdigest()
            cached = cache.get(key)
            if cached is not None:
                return cached
            result = fn(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

# Usage
# @cache_result(ttl=600)
# def get_active_plans():
#     return list(Plan.objects.filter(active=True).values())