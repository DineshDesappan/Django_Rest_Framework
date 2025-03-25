from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class StreamThrottleAnon(AnonRateThrottle):
    scope = 'streamanon'
    
class StreamThrottleUser(UserRateThrottle):
    scope = 'streamuser'