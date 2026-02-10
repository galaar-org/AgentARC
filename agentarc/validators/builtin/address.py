"""
Address-based validators (denylist and allowlist).

These validators check transaction destination addresses
against configured lists.
"""

from typing import TYPE_CHECKING

from ..base import PolicyValidator, ValidationResult
from ..registry import ValidatorRegistry

if TYPE_CHECKING:
    from ...calldata_parser import ParsedTransaction


@ValidatorRegistry.register("address_denylist")
class AddressDenylistValidator(PolicyValidator):
    """
    Block transactions to/from denied addresses.

    Configuration:
        type: "address_denylist"
        denied_addresses: List of addresses to block
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "address_denylist",
        ...     "denied_addresses": ["0xbad...", "0xmalicious..."],
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if transaction targets a denied address."""
        if not self.enabled:
            return ValidationResult(passed=True)

        denied_addresses = [addr.lower() for addr in self.config.get("denied_addresses", [])]

        if not denied_addresses:
            return ValidationResult(passed=True)

        # Check destination address
        if parsed_tx.to and parsed_tx.to.lower() in denied_addresses:
            return ValidationResult(
                passed=False,
                reason=f"Destination address {parsed_tx.to} is on denylist",
                rule_name="address_denylist",
            )

        # Check extracted recipient (for token transfers)
        if parsed_tx.recipient_address and parsed_tx.recipient_address.lower() in denied_addresses:
            return ValidationResult(
                passed=False,
                reason=f"Recipient address {parsed_tx.recipient_address} is on denylist",
                rule_name="address_denylist",
            )

        return ValidationResult(passed=True)


@ValidatorRegistry.register("address_allowlist")
class AddressAllowlistValidator(PolicyValidator):
    """
    Only allow transactions to approved addresses.

    If the allowlist is empty, all addresses are allowed.
    If the allowlist has entries, only those addresses are allowed.

    Configuration:
        type: "address_allowlist"
        allowed_addresses: List of allowed addresses (empty = allow all)
        enabled: Whether policy is active

    Example config:
        >>> config = {
        ...     "type": "address_allowlist",
        ...     "allowed_addresses": ["0xsafe...", "0xapproved..."],
        ...     "enabled": True
        ... }
    """

    def validate(self, parsed_tx: "ParsedTransaction") -> ValidationResult:
        """Check if transaction targets an allowed address."""
        if not self.enabled:
            return ValidationResult(passed=True)

        allowed_addresses = [addr.lower() for addr in self.config.get("allowed_addresses", [])]

        # If allowlist is empty, allow all
        if not allowed_addresses:
            return ValidationResult(passed=True)

        # Check recipient - use extracted recipient if available, otherwise use 'to'
        recipient = parsed_tx.recipient_address or parsed_tx.to

        if recipient and recipient.lower() not in allowed_addresses:
            return ValidationResult(
                passed=False,
                reason=f"Address {recipient} is not on allowlist",
                rule_name="address_allowlist",
            )

        return ValidationResult(passed=True)
