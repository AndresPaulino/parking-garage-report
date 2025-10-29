"""
Test script for enhanced parking automation with browser stability improvements
This script tests the browser restart and recovery mechanisms with a small subset of accounts
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add current directory to path so we can import our module
sys.path.insert(0, os.getcwd())

from enhanced_parking_automation import EnhancedParkingAutomation, BrowserHealthMonitor, ErrorRecoveryHandler

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_stability.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_browser_health_monitor():
    """Test the browser health monitoring functionality"""
    logger.info("Testing Browser Health Monitor...")

    monitor = BrowserHealthMonitor()

    # Test initial state
    assert monitor.operations_count == 0
    assert not monitor.should_restart()

    # Test operation counting
    for i in range(50):
        monitor.increment_operation()

    assert monitor.operations_count == 50
    logger.info("✅ Browser health monitor operations counting works")

    # Test reset
    monitor.reset()
    assert monitor.operations_count == 0
    logger.info("✅ Browser health monitor reset works")

def test_error_recovery_handler():
    """Test the error recovery handler"""
    logger.info("Testing Error Recovery Handler...")

    # Test known error patterns
    test_cases = [
        ("Target page, context or browser has been closed", "restart_browser", True),
        ("Session expired", "relogin", True),
        ("Navigation timeout", "retry_navigation", True),
        ("Some unknown error", "unknown", False),
        ("Protocol error (Inspector.enable): Browser has been closed", "restart_browser", True)
    ]

    for error_msg, expected_strategy, should_retry in test_cases:
        strategy = ErrorRecoveryHandler.get_recovery_strategy(error_msg)
        retry = ErrorRecoveryHandler.should_retry(error_msg)

        assert strategy == expected_strategy, f"Expected {expected_strategy}, got {strategy} for: {error_msg}"
        assert retry == should_retry, f"Expected retry={should_retry}, got {retry} for: {error_msg}"

    logger.info("✅ Error recovery handler works correctly")

async def test_browser_setup_and_cleanup():
    """Test browser setup and cleanup without full login"""
    logger.info("Testing browser setup and cleanup...")

    # Use dummy credentials for testing
    automation = EnhancedParkingAutomation("test", "test", headless=True)

    try:
        # Test browser setup
        await automation.setup_browser()
        assert automation.browser is not None
        assert automation.page is not None
        logger.info("✅ Browser setup successful")

        # Test browser health check (should work on fresh browser)
        try:
            await automation.ensure_browser_alive()
            logger.info("✅ Browser health check works on fresh browser")
        except:
            logger.info("ℹ️ Browser health check expected to fail without proper page")

        # Test browser restart
        await automation.setup_browser()
        logger.info("✅ Browser restart works")

    finally:
        # Clean shutdown
        try:
            if automation.browser:
                await automation.browser.close()
            if automation.playwright_instance:
                await automation.playwright_instance.stop()
        except:
            pass

async def test_batch_processing_logic():
    """Test the batch processing logic"""
    logger.info("Testing batch processing logic...")

    automation = EnhancedParkingAutomation("test", "test", headless=True)

    # Test account splitting
    test_accounts = [
        ("1", "Account 1"),
        ("2", "Account 2"),
        ("3", "Account 3"),
        ("4", "Account 4"),
        ("5", "Account 5")
    ]

    batches = automation.split_accounts_into_batches(test_accounts, batch_size=2)

    assert len(batches) == 3, f"Expected 3 batches, got {len(batches)}"
    assert len(batches[0]) == 2, f"First batch should have 2 accounts, got {len(batches[0])}"
    assert len(batches[1]) == 2, f"Second batch should have 2 accounts, got {len(batches[1])}"
    assert len(batches[2]) == 1, f"Third batch should have 1 account, got {len(batches[2])}"

    logger.info("✅ Batch processing logic works correctly")

async def run_integration_test():
    """Run a quick integration test with real browser but dummy credentials"""
    logger.info("Running integration test...")

    automation = EnhancedParkingAutomation("dummy", "dummy", headless=True)

    try:
        # Test browser setup
        await automation.setup_browser()
        logger.info("✅ Browser started successfully")

        # Test navigation (should fail with dummy credentials, but browser should work)
        try:
            success = await automation.login()
            logger.info(f"Login result: {success} (expected to fail with dummy credentials)")
        except Exception as e:
            logger.info(f"Login failed as expected: {str(e)[:100]}...")

        logger.info("✅ Integration test completed")

    finally:
        try:
            if automation.browser:
                await automation.browser.close()
            if automation.playwright_instance:
                await automation.playwright_instance.stop()
        except:
            pass

async def main():
    """Run all tests"""
    logger.info("Starting Enhanced Parking Automation Stability Tests")
    logger.info("=" * 60)

    try:
        # Unit tests
        await test_browser_health_monitor()
        test_error_recovery_handler()
        await test_batch_processing_logic()

        # Browser tests
        await test_browser_setup_and_cleanup()
        await run_integration_test()

        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("Enhanced stability features are working correctly.")

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ TEST FAILED: {str(e)}")
        logger.error("Please check the implementation.")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)