from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for account activation emails.
    Creates secure, time-limited tokens for email verification.
    """
    TIMEOUT_DAYS = 1  # 24-hour expiration

    def _make_hash_value(self, user, timestamp):
        """
        Create hash value using user's pk, email, is_active status, and timestamp.
        This ensures tokens become invalid once the user is activated.
        """
        return (
            str(user.pk) +
            str(user.email) +
            str(user.is_active) +
            str(timestamp)
        )

    def _get_token_timeout(self):
        """Set token expiration to 24 hours (TIMEOUT_DAYS)."""
        return timezone.timedelta(days=self.TIMEOUT_DAYS)

    def check_token(self, user, token):
        """Check if the token is valid and the user is not already active."""
        if user.is_active:
            return False
        return super().check_token(user, token)

# Create an instance
account_activation_token = AccountActivationTokenGenerator()