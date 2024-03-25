#################################################################################
# WaterTAP Copyright (c) 2020-2024, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National Laboratory,
# National Renewable Energy Laboratory, and National Energy Technology
# Laboratory (subject to receipt of any required approvals from the U.S. Dept.
# of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#################################################################################
import pytest
from pyomo.environ import (
    value,
    assert_optimal_termination,
)
from idaes.core.solvers import get_solver
from watertap.core.util.initialization import assert_degrees_of_freedom
from pyomo.util.check_units import assert_units_consistent
from watertap.examples.flowsheets.case_studies.wastewater_resource_recovery.dye_desalination.dye_desalination_withRO import (
    build,
    set_operating_conditions,
    initialize_system,
    initialize_costing,
    solve,
    add_costing,
    optimize_operation,
    display_results,
    display_costing,
)

solver = get_solver()


class TestDyewithROFlowsheetwithPretreatment:
    @pytest.fixture(scope="class")
    def system_frame(self):
        m = build(include_pretreatment=True)
        return m

    @pytest.mark.unit
    def test_build(self, system_frame):
        m = system_frame
        assert_degrees_of_freedom(m, 28)
        assert_units_consistent(m)

    @pytest.mark.component
    def test_set_operating_conditions(self, system_frame):
        m = system_frame
        set_operating_conditions(m)
        initialize_system(m)

        # test feed
        assert pytest.approx(77.607, rel=1e-3) == value(
            m.fs.feed.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "tds"])

        assert pytest.approx(0.2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "dye"])

        # test wwtp
        assert pytest.approx(0.14, rel=1e-5) == value(
            m.fs.pretreatment.wwtp.energy_electric_flow_vol_inlet
        )

        # test pump block
        assert pytest.approx(7, rel=1e-5) == value(
            m.fs.dye_separation.P1.applied_pressure[0]
        )

        # test nanofiltration
        assert pytest.approx(315.9843, rel=1e-5) == value(
            m.fs.dye_separation.nanofiltration.area
        )

        # check products
        assert pytest.approx(0, rel=1e-6) == value(
            m.fs.wwt_retentate.flow_mass_comp[0, "dye"]
        )
        assert pytest.approx(0.026809, rel=1e-3) == value(
            m.fs.dye_retentate.flow_mass_comp[0, "tds"]
        )

        assert pytest.approx(0.965, rel=1e-5) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(0.035, rel=1e-5) == value(
            m.fs.brine.flow_mass_phase_comp[0, "Liq", "TDS"]
        )

    @pytest.mark.component
    def test_solve(self, system_frame):
        m = system_frame

        results = solve(m)

        # check products
        assert pytest.approx(0.02894, rel=1e-3) == value(
            m.fs.wwt_retentate.flow_mass_comp[0, "tds"]
        )
        assert pytest.approx(13.1931, rel=1e-3) == value(
            m.fs.dye_retentate.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(32.2185, rel=1e-5) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(32.1950, rel=1e-5) == value(
            m.fs.brine.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

    @pytest.mark.component
    def test_costing(self, system_frame):
        m = system_frame

        add_costing(m)
        initialize_costing(m)
        optimize_operation(m)

        results = solve(m)
        assert_optimal_termination(results)

        # check costing
        assert pytest.approx(27.821289, rel=1e-3) == value(m.fs.LCOW)
        assert pytest.approx(19.835558, rel=1e-3) == value(m.fs.LCOT)

    @pytest.mark.component
    def test_display(self, system_frame):
        m = system_frame
        display_results(m)
        display_costing(m)


class TestDyewithROFlowsheetDefault:
    @pytest.fixture(scope="class")
    def system_frame(self):
        m = build()
        return m

    @pytest.mark.unit
    def test_build(self, system_frame):
        m = system_frame
        assert_degrees_of_freedom(m, 24)
        assert_units_consistent(m)

    @pytest.mark.component
    def test_set_operating_conditions(self, system_frame):
        m = system_frame
        set_operating_conditions(m)
        initialize_system(m)

        # test feed
        assert pytest.approx(77.607, rel=1e-3) == value(
            m.fs.feed.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "tds"])

        assert pytest.approx(0.2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "dye"])

        # test pump block
        assert pytest.approx(7, rel=1e-5) == value(
            m.fs.dye_separation.P1.applied_pressure[0]
        )

        # test nanofiltration
        assert pytest.approx(316.096, rel=1e-5) == value(
            m.fs.dye_separation.nanofiltration.area
        )

        # check products
        assert pytest.approx(0.032937, rel=1e-3) == value(
            m.fs.dye_retentate.flow_mass_comp[0, "tds"]
        )

        assert pytest.approx(0.965, rel=1e-5) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(0.035, rel=1e-5) == value(
            m.fs.brine.flow_mass_phase_comp[0, "Liq", "TDS"]
        )

    @pytest.mark.component
    def test_solve(self, system_frame):
        m = system_frame

        results = solve(m)

        # check products
        assert pytest.approx(13.1931, rel=1e-3) == value(
            m.fs.dye_retentate.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(32.2212, rel=1e-5) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(32.1923, rel=1e-5) == value(
            m.fs.brine.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

    def test_costing(self, system_frame):
        m = system_frame

        add_costing(m)
        initialize_costing(m)
        optimize_operation(m)

        results = solve(m)
        assert_optimal_termination(results)

        # check costing
        assert pytest.approx(27.719244, rel=1e-3) == value(m.fs.LCOW)
        assert pytest.approx(19.774679, rel=1e-3) == value(m.fs.LCOT)

    @pytest.mark.component
    def test_display(self, system_frame):
        m = system_frame
        display_results(m)
        display_costing(m)


class TestDyewithROFlowsheetwithDewatering:
    @pytest.fixture(scope="class")
    def system_frame(self):
        m = build(include_dewatering=True)
        return m

    @pytest.mark.unit
    def test_build(self, system_frame):
        m = system_frame
        assert_degrees_of_freedom(m, 27)
        assert_units_consistent(m)

    @pytest.mark.component
    def test_set_operating_conditions(self, system_frame):
        m = system_frame
        set_operating_conditions(m)
        initialize_system(m)

        # test feed
        assert pytest.approx(77.607, rel=1e-3) == value(
            m.fs.feed.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "tds"])

        assert pytest.approx(0.2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "dye"])

        # test dewaterer block
        assert pytest.approx(0.99, rel=1e-5) == value(
            m.fs.dewaterer.split_fraction[0, "precipitant", "dye"]
        )

        # test pump block
        assert pytest.approx(7, rel=1e-5) == value(
            m.fs.dye_separation.P1.applied_pressure[0]
        )

        # test nanofiltration
        assert pytest.approx(316.0961, rel=1e-5) == value(
            m.fs.dye_separation.nanofiltration.area
        )

        # check products
        assert pytest.approx(1, rel=1e-3) == value(
            m.fs.precipitant.flow_mass_comp[0, "tds"]
        )

        assert pytest.approx(0.965, rel=1e-5) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(0.035, rel=1e-5) == value(
            m.fs.brine.flow_mass_phase_comp[0, "Liq", "TDS"]
        )

    @pytest.mark.component
    @pytest.mark.requires_idaes_solver
    def test_solve(self, system_frame):
        m = system_frame

        results = solve(m)

        # check products
        assert pytest.approx(13.0612, rel=1e-3) == value(
            m.fs.centrate.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(0.131931, rel=1e-3) == value(
            m.fs.precipitant.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(32.2212, rel=1e-5) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(32.1923, rel=1e-5) == value(
            m.fs.brine.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

    @pytest.mark.component
    @pytest.mark.requires_idaes_solver
    def test_costing(self, system_frame):
        m = system_frame

        add_costing(m)
        initialize_costing(m)
        optimize_operation(m)

        results = solve(m)
        assert_optimal_termination(results)

        # check costing
        assert pytest.approx(1.08502, rel=1e-3) == value(m.fs.LCOW)
        assert pytest.approx(-0.151027, rel=1e-3) == value(m.fs.LCOT)

    @pytest.mark.component
    @pytest.mark.requires_idaes_solver
    def test_display(self, system_frame):
        m = system_frame
        display_results(m)
        display_costing(m)


class TestDyewithROFlowsheetwithGAC:
    @pytest.fixture(scope="class")
    def system_frame(self):
        m = build(include_gac=True)
        return m

    @pytest.mark.unit
    def test_build(self, system_frame):
        m = system_frame
        assert_degrees_of_freedom(m, 43)

    @pytest.mark.component
    def test_set_operating_conditions(self, system_frame):
        m = system_frame
        set_operating_conditions(m)
        assert_units_consistent(m)
        initialize_system(m)

        # test feed
        assert pytest.approx(77.607, rel=1e-3) == value(
            m.fs.feed.flow_mass_comp[0, "H2O"]
        )

        assert pytest.approx(2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "tds"])

        assert pytest.approx(0.2, rel=1e-5) == value(m.fs.feed.conc_mass_comp[0, "dye"])

        # test pump block
        assert pytest.approx(7, rel=1e-5) == value(
            m.fs.dye_separation.P1.applied_pressure[0]
        )

        # test nanofiltration
        assert pytest.approx(316.0961, rel=1e-5) == value(
            m.fs.dye_separation.nanofiltration.area
        )

    @pytest.mark.component
    @pytest.mark.requires_idaes_solver
    def test_solve(self, system_frame):
        m = system_frame

        results = solve(m)

        # check products
        assert pytest.approx(32.22122, rel=1e-6) == value(
            m.fs.permeate.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(13.19313, rel=1e-3) == value(
            m.fs.treated.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(0.000504058, rel=1e-3) == value(
            m.fs.treated.flow_mass_phase_comp[0, "Liq", "dye"]
        )

        assert pytest.approx(0.0329367, rel=1e-3) == value(
            m.fs.treated.flow_mass_phase_comp[0, "Liq", "tds"]
        )

        assert pytest.approx(0, rel=1e-3) == value(
            m.fs.adsorbed_dye.flow_mass_phase_comp[0, "Liq", "H2O"]
        )

        assert pytest.approx(0.0149224, rel=1e-3) == value(
            m.fs.adsorbed_dye.flow_mass_phase_comp[0, "Liq", "dye"]
        )

        assert pytest.approx(0, rel=1e-3) == value(
            m.fs.adsorbed_dye.flow_mass_phase_comp[0, "Liq", "tds"]
        )

    @pytest.mark.component
    @pytest.mark.requires_idaes_solver
    def test_costing(self, system_frame):
        m = system_frame

        add_costing(m)
        initialize_costing(m)
        optimize_operation(m)

        results = solve(m)
        assert_optimal_termination(results)

        # check costing
        assert pytest.approx(0.415656, rel=1e-3) == value(m.fs.LCOW)
        assert pytest.approx(-0.765208, rel=1e-3) == value(m.fs.LCOT)

    @pytest.mark.component
    @pytest.mark.requires_idaes_solver
    def test_display(self, system_frame):
        m = system_frame
        display_results(m)
        display_costing(m)
