"""
Tests for exceptions module.

Tests all custom NIMA exceptions including:
- Base NimaError
- AffectVectorError and subclasses
- Message formatting with context
- Exception hierarchy
- Catch-all handling via NimaError

Author: NIMA Core Team
Date: Feb 13, 2026
"""

import pytest
from nima_core.cognition.exceptions import (
    NimaError,
    AffectVectorError,
    InvalidAffectNameError,
    AffectValueError,
    BaselineValidationError,
    StatePersistenceError,
    ProfileNotFoundError,
    EmotionDetectionError,
    ArchetypeError,
    UnknownArchetypeError,
)


class TestNimaError:
    """Test base NimaError exception."""
    
    def test_can_be_raised(self):
        """NimaError can be raised with a message."""
        with pytest.raises(NimaError, match="test message"):
            raise NimaError("test message")
    
    def test_is_exception(self):
        """NimaError inherits from Exception."""
        assert issubclass(NimaError, Exception)
    
    def test_can_be_caught(self):
        """NimaError can be caught."""
        try:
            raise NimaError("test")
        except NimaError as e:
            assert str(e) == "test"


class TestAffectVectorError:
    """Test AffectVectorError exception."""
    
    def test_inherits_from_nima_error(self):
        """AffectVectorError inherits from NimaError."""
        assert issubclass(AffectVectorError, NimaError)
    
    def test_can_be_raised(self):
        """AffectVectorError can be raised with a message."""
        with pytest.raises(AffectVectorError, match="invalid vector"):
            raise AffectVectorError("invalid vector")
    
    def test_can_be_caught_as_nima_error(self):
        """AffectVectorError can be caught as NimaError."""
        try:
            raise AffectVectorError("test")
        except NimaError as e:
            assert isinstance(e, AffectVectorError)


class TestInvalidAffectNameError:
    """Test InvalidAffectNameError exception."""
    
    def test_inherits_from_affect_vector_error(self):
        """InvalidAffectNameError inherits from AffectVectorError."""
        assert issubclass(InvalidAffectNameError, AffectVectorError)
    
    def test_inherits_from_nima_error(self):
        """InvalidAffectNameError inherits from NimaError."""
        assert issubclass(InvalidAffectNameError, NimaError)
    
    def test_message_includes_invalid_name(self):
        """Error message includes the invalid affect name."""
        with pytest.raises(InvalidAffectNameError, match="INVALID"):
            raise InvalidAffectNameError("INVALID")
    
    def test_message_includes_valid_names(self):
        """Error message includes valid affect names when provided."""
        valid = ["SEEKING", "RAGE", "FEAR"]
        
        with pytest.raises(InvalidAffectNameError, match="SEEKING.*RAGE.*FEAR"):
            raise InvalidAffectNameError("INVALID", valid_names=valid)
    
    def test_stores_attributes(self):
        """Exception stores name and valid_names attributes."""
        valid = ["SEEKING", "RAGE"]
        exc = InvalidAffectNameError("BAD", valid_names=valid)
        
        assert exc.name == "BAD"
        assert exc.valid_names == valid
    
    def test_without_valid_names(self):
        """Exception works without valid_names list."""
        exc = InvalidAffectNameError("BAD")
        
        assert exc.name == "BAD"
        assert exc.valid_names is None
        assert "BAD" in str(exc)


class TestAffectValueError:
    """Test AffectValueError exception."""
    
    def test_inherits_from_affect_vector_error(self):
        """AffectValueError inherits from AffectVectorError."""
        assert issubclass(AffectValueError, AffectVectorError)
    
    def test_message_includes_affect_name(self):
        """Error message includes affect name."""
        with pytest.raises(AffectValueError, match="FEAR"):
            raise AffectValueError("FEAR", 1.5)
    
    def test_message_includes_value(self):
        """Error message includes the invalid value."""
        with pytest.raises(AffectValueError, match="1.5"):
            raise AffectValueError("FEAR", 1.5)
    
    def test_message_includes_valid_range(self):
        """Error message includes valid range [0, 1]."""
        with pytest.raises(AffectValueError, match=r"\[0, 1\]"):
            raise AffectValueError("FEAR", -0.5)
    
    def test_stores_attributes(self):
        """Exception stores affect and value attributes."""
        exc = AffectValueError("PLAY", 2.0)
        
        assert exc.affect == "PLAY"
        assert exc.value == 2.0
    
    def test_negative_value(self):
        """Exception works with negative values."""
        exc = AffectValueError("RAGE", -0.3)
        
        assert exc.value == -0.3
        assert "-0.3" in str(exc)


class TestBaselineValidationError:
    """Test BaselineValidationError exception."""
    
    def test_inherits_from_affect_vector_error(self):
        """BaselineValidationError inherits from AffectVectorError."""
        assert issubclass(BaselineValidationError, AffectVectorError)
    
    def test_message_format(self):
        """Error message includes 'Invalid baseline' prefix."""
        with pytest.raises(BaselineValidationError, match="Invalid baseline"):
            raise BaselineValidationError("wrong dimension")
    
    def test_includes_reason(self):
        """Error message includes the reason."""
        reason = "must be 7D vector"
        with pytest.raises(BaselineValidationError, match=reason):
            raise BaselineValidationError(reason)


class TestStatePersistenceError:
    """Test StatePersistenceError exception."""
    
    def test_inherits_from_nima_error(self):
        """StatePersistenceError inherits from NimaError."""
        assert issubclass(StatePersistenceError, NimaError)
    
    def test_message_includes_path(self):
        """Error message includes file path."""
        path = "/tmp/state.json"
        with pytest.raises(StatePersistenceError, match=path):
            raise StatePersistenceError(path, "save", "permission denied")
    
    def test_message_includes_operation(self):
        """Error message includes operation (save/load)."""
        with pytest.raises(StatePersistenceError, match="save"):
            raise StatePersistenceError("/tmp/state.json", "save", "disk full")
    
    def test_message_includes_reason(self):
        """Error message includes reason for failure."""
        reason = "file not found"
        with pytest.raises(StatePersistenceError, match=reason):
            raise StatePersistenceError("/tmp/state.json", "load", reason)
    
    def test_stores_attributes(self):
        """Exception stores path, operation, and reason."""
        exc = StatePersistenceError("/data/state.pkl", "load", "corrupted")
        
        assert exc.path == "/data/state.pkl"
        assert exc.operation == "load"
        assert exc.reason == "corrupted"


class TestProfileNotFoundError:
    """Test ProfileNotFoundError exception."""
    
    def test_inherits_from_nima_error(self):
        """ProfileNotFoundError inherits from NimaError."""
        assert issubclass(ProfileNotFoundError, NimaError)
    
    def test_message_includes_profile_name(self):
        """Error message includes missing profile name."""
        with pytest.raises(ProfileNotFoundError, match="unknown_profile"):
            raise ProfileNotFoundError("unknown_profile")
    
    def test_message_includes_available_list(self):
        """Error message includes available profiles."""
        available = ["default", "creative", "analytical"]
        
        with pytest.raises(ProfileNotFoundError, match="default.*creative.*analytical"):
            raise ProfileNotFoundError("bad", available=available)
    
    def test_stores_attributes(self):
        """Exception stores profile_name and available."""
        available = ["a", "b"]
        exc = ProfileNotFoundError("c", available=available)
        
        assert exc.profile_name == "c"
        assert exc.available == available


class TestEmotionDetectionError:
    """Test EmotionDetectionError exception."""
    
    def test_inherits_from_nima_error(self):
        """EmotionDetectionError inherits from NimaError."""
        assert issubclass(EmotionDetectionError, NimaError)
    
    def test_can_be_raised(self):
        """EmotionDetectionError can be raised with a message."""
        with pytest.raises(EmotionDetectionError, match="detection failed"):
            raise EmotionDetectionError("detection failed")


class TestArchetypeError:
    """Test ArchetypeError exception."""
    
    def test_inherits_from_nima_error(self):
        """ArchetypeError inherits from NimaError."""
        assert issubclass(ArchetypeError, NimaError)
    
    def test_can_be_raised(self):
        """ArchetypeError can be raised with a message."""
        with pytest.raises(ArchetypeError, match="archetype error"):
            raise ArchetypeError("archetype error")


class TestUnknownArchetypeError:
    """Test UnknownArchetypeError exception."""
    
    def test_inherits_from_archetype_error(self):
        """UnknownArchetypeError inherits from ArchetypeError."""
        assert issubclass(UnknownArchetypeError, ArchetypeError)
    
    def test_inherits_from_nima_error(self):
        """UnknownArchetypeError inherits from NimaError."""
        assert issubclass(UnknownArchetypeError, NimaError)
    
    def test_message_includes_name(self):
        """Error message includes unknown archetype name."""
        with pytest.raises(UnknownArchetypeError, match="badarch"):
            raise UnknownArchetypeError("badarch")
    
    def test_message_includes_available(self):
        """Error message includes available archetypes."""
        available = ["hero", "sage", "rebel"]
        
        with pytest.raises(UnknownArchetypeError, match="hero.*sage.*rebel"):
            raise UnknownArchetypeError("bad", available=available)
    
    def test_stores_attributes(self):
        """Exception stores name and available."""
        available = ["x", "y"]
        exc = UnknownArchetypeError("z", available=available)
        
        assert exc.name == "z"
        assert exc.available == available


class TestExceptionHierarchy:
    """Test exception inheritance chain."""
    
    def test_all_inherit_from_nima_error(self):
        """All custom exceptions inherit from NimaError."""
        exceptions = [
            AffectVectorError,
            InvalidAffectNameError,
            AffectValueError,
            BaselineValidationError,
            StatePersistenceError,
            ProfileNotFoundError,
            EmotionDetectionError,
            ArchetypeError,
            UnknownArchetypeError,
        ]
        
        for exc in exceptions:
            assert issubclass(exc, NimaError), f"{exc.__name__} should inherit from NimaError"
    
    def test_affect_errors_inherit_from_affect_vector_error(self):
        """Affect-related errors inherit from AffectVectorError."""
        affect_errors = [
            InvalidAffectNameError,
            AffectValueError,
            BaselineValidationError,
        ]
        
        for exc in affect_errors:
            assert issubclass(exc, AffectVectorError)
    
    def test_can_catch_all_as_nima_error(self):
        """All exceptions can be caught as NimaError."""
        exceptions = [
            AffectVectorError("test"),
            InvalidAffectNameError("BAD"),
            AffectValueError("FEAR", 2.0),
            BaselineValidationError("reason"),
            StatePersistenceError("/path", "save", "error"),
            ProfileNotFoundError("bad"),
            EmotionDetectionError("fail"),
            ArchetypeError("test"),
            UnknownArchetypeError("bad"),
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except NimaError as e:
                assert isinstance(e, type(exc))
    
    def test_specific_catches_work(self):
        """Specific exception types can be caught individually."""
        # Test catching specific type
        try:
            raise InvalidAffectNameError("BAD")
        except InvalidAffectNameError as e:
            assert e.name == "BAD"
        
        # Test catching parent type
        try:
            raise InvalidAffectNameError("BAD")
        except AffectVectorError as e:
            assert isinstance(e, InvalidAffectNameError)
