import pytest

from gsy_framework.sim_results.energy_trade_profile import EnergyTradeProfile


class TestEnergyTradeProfile:
    """Test the EnergyTradeProfile class interfaces."""
    @staticmethod
    @pytest.fixture(name="test_constants")
    def fixture_constants():
        """Global constants to be used and extended within tests."""

        return {
            "seller_area_name": "seller", "seller_area_uuid": "uuid1",
            "trade_energy": 10, "market_slot": "2022-01-04T12:12",
            "buyer_area_name": "buyer"}

    @staticmethod
    @pytest.fixture(name="area_result_dict")
    def fixture_area_result_dict(test_constants):
        """Basic area_results_dict argument."""
        return {
            "name": test_constants["seller_area_name"],
            "uuid": test_constants["seller_area_uuid"],
            "children": []}

    @staticmethod
    @pytest.fixture(name="core_stats")
    def fixture_core_stats(test_constants):
        """Basic core_stats argument."""
        return {
            test_constants["seller_area_uuid"]: {"trades": [
                {"seller": test_constants["seller_area_name"],
                 "buyer": test_constants["buyer_area_name"],
                 "energy": test_constants["trade_energy"]}]}}

    @staticmethod
    def test_update_should_export_plots_empty_update_parameters():
        """Test whether passing empty arguments will nullify the side effects of update()."""

        energy_trade_profile = EnergyTradeProfile(should_export_plots=True)
        # We did not pass the needed update parameters
        energy_trade_profile.update()
        assert energy_trade_profile.traded_energy_profile == {}
        assert energy_trade_profile.traded_energy_current == {}

    @staticmethod
    def test_update_should_export_plots_correctly_updates_traded_energy(
            area_result_dict, core_stats, test_constants):
        """Test whether the update() method correctly sets the traded energy profiles."""

        energy_trade_profile = EnergyTradeProfile(should_export_plots=True)
        energy_trade_profile.update(
            area_result_dict, core_stats, test_constants["market_slot"])
        assert (
                energy_trade_profile.traded_energy_profile ==
                energy_trade_profile.traded_energy_current == {
                    test_constants["seller_area_name"]: {
                        "bought_energy": {
                            test_constants["buyer_area_name"]: {
                                test_constants["seller_area_name"]: {
                                    "January 04 2022, 12:12 h": 10},
                                "accumulated": {
                                    "January 04 2022, 12:12 h": test_constants[
                                        "trade_energy"]}}},
                        "sold_energy": {
                            test_constants["seller_area_name"]: {
                                test_constants["buyer_area_name"]: {
                                    "January 04 2022, 12:12 h": test_constants[
                                        "trade_energy"]},
                                "accumulated": {
                                    "January 04 2022, 12:12 h": test_constants[
                                        "trade_energy"]}}}}})

    @staticmethod
    def test_update_should_not_export_plots_correctly_updates_traded_energy(
            area_result_dict, core_stats, test_constants):
        """Test whether the update() method correctly sets the traded energy profiles."""

        energy_trade_profile = EnergyTradeProfile(should_export_plots=False)
        energy_trade_profile.update(
            area_result_dict, core_stats, test_constants["market_slot"])
        assert energy_trade_profile.traded_energy_profile == {}
        assert (
                energy_trade_profile.traded_energy_current == {
                    # The key here should be equal to the uuid instead of name
                    test_constants["seller_area_uuid"]: {
                        "bought_energy": {
                            test_constants["buyer_area_name"]: {
                                test_constants["seller_area_name"]: {
                                    "January 04 2022, 12:12 h": 10},
                                "accumulated": {
                                    "January 04 2022, 12:12 h": test_constants[
                                        "trade_energy"]}}},
                        "sold_energy": {
                            test_constants["seller_area_name"]: {
                                test_constants["buyer_area_name"]: {
                                    "January 04 2022, 12:12 h": test_constants[
                                        "trade_energy"]},
                                "accumulated": {
                                    "January 04 2022, 12:12 h": test_constants[
                                        "trade_energy"]}}}}})
