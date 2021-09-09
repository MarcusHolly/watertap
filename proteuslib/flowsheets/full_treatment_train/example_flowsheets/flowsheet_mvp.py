###############################################################################
# ProteusLib Copyright (c) 2021, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National
# Laboratory, National Renewable Energy Laboratory, and National Energy
# Technology Laboratory (subject to receipt of any required approvals from
# the U.S. Dept. of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/nawi-hub/proteuslib/"
#
###############################################################################

from pyomo.environ import ConcreteModel, Objective, Expression, Constraint, TransformationFactory, value, Block
from pyomo.network import Arc
from pyomo.util import infeasible
from idaes.core import FlowsheetBlock
from idaes.core.util.scaling import (calculate_scaling_factors,
                                     constraint_autoscale_large_jac)
from idaes.core.util.initialization import propagate_state
from proteuslib.flowsheets.full_treatment_train.example_flowsheets import (pretreatment,
                                                                           desalination,
                                                                           translator_block,
                                                                           feed_block,
                                                                           gypsum_saturation_index)
from proteuslib.flowsheets.full_treatment_train.example_models import property_models
from proteuslib.flowsheets.full_treatment_train.util import (solve_with_user_scaling,
                                                             check_dof)

"""Flowsheet examples that satisfy minimum viable product requirements"""
def build_flowsheet_mvp_NF(m, has_bypass=True, has_desal_feed=False, is_twostage=False,
                               NF_type='ZO', NF_base='ion',
                               RO_type='Sep', RO_base='TDS', RO_level='simple'):
    """
    Build a flowsheet with NF pretreatment and RO.
    """
    # set up keyword arguments for the sections of treatment train
    # kwargs_pretreatment = {'has_bypass': has_bypass, 'NF_type': NF_type, 'NF_base': NF_base}
    kwargs_desalination = {'has_desal_feed': has_desal_feed, 'is_twostage': is_twostage,
                           'RO_type': RO_type, 'RO_base': RO_base, 'RO_level': RO_level}
    # build flowsheet
    property_models.build_prop(m, base='ion')
    feed_block.build_feed(m, base='ion')
    m.fs.feed.properties[0].flow_mol_phase_comp
    pretrt_port = {'out': m.fs.feed.outlet}
    # pretrt_port = pretreatment.build_pretreatment_NF(m, **kwargs_pretreatment)

    property_models.build_prop(m, base=RO_base)
    desal_port = desalination.build_desalination(m, **kwargs_desalination)

    property_models.build_prop(m, base='eNRTL')

    translator_block.build_tb(m, base_inlet=NF_base, base_outlet=RO_base, name_str='tb_pretrt_to_desal')

    # set up Arcs between pretreatment and desalination
    m.fs.s_pretrt_tb = Arc(source=pretrt_port['out'], destination=m.fs.tb_pretrt_to_desal.inlet)
    m.fs.s_tb_desal = Arc(source=m.fs.tb_pretrt_to_desal.outlet, destination=desal_port['in'])

    gypsum_saturation_index.build_desalination_saturation(m, **kwargs_desalination)

    return m


def solve_flowsheet_mvp_NF(**kwargs):
    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    build_flowsheet_mvp_NF(m, **kwargs)
    TransformationFactory("network.expand_arcs").apply_to(m)

    # scale
    # pretreatment.scale_pretreatment_NF(m, **kwargs)
    calculate_scaling_factors(m.fs.tb_pretrt_to_desal)
    desalination.scale_desalination(m, **kwargs)
    calculate_scaling_factors(m)

    # initialize
    optarg = {'nlp_scaling_method': 'user-scaling'}
    # pretreatment.initialize_pretreatment_NF(m, **kwargs)
    propagate_state(m.fs.s_pretrt_tb)
    m.fs.tb_pretrt_to_desal.initialize(optarg=optarg)
    propagate_state(m.fs.s_tb_desal)
    desalination.initialize_desalination(m, **kwargs)
    m.fs.desal_saturation.properties.initialize()
    # assert False

    check_dof(m)
    # solve_without_user_scaling(m, tee=False, fail_flag=False)
    # solve_without_user_scaling(m, tee=False, fail_flag=True)
    solve_with_user_scaling(m, tee=False, fail_flag=True)

    # pretreatment.display_pretreatment_NF(m, **kwargs)
    m.fs.feed.report()
    m.fs.tb_pretrt_to_desal.report()
    desalination.display_desalination(m, **kwargs)
    # m.fs.desal_saturation.properties.display()
    print('Solubility index:', value(m.fs.desal_saturation.saturation_index))
    m.fs.desal_saturation.properties[0].flow_mol.display()
    m.fs.desal_saturation.properties[0].mole_frac_comp.display()

    # solve #2
    m.fs.RO.area.fix(60)
    m.fs.pump_RO.control_volume.properties_out[0].pressure.fix(50e5)
    solve_with_user_scaling(m, tee=False, fail_flag=True)

    # m.fs.feed.report()
    # m.fs.tb_pretrt_to_desal.report()
    desalination.display_desalination(m, **kwargs)
    # m.fs.desal_saturation.properties.display()
    print('Flux:', value(m.fs.RO.flux_mass_phase_comp_avg[0, 'Liq', 'H2O']) * 3600)
    print('Solubility index:', value(m.fs.desal_saturation.saturation_index))
    m.fs.desal_saturation.properties[0].flow_mol.display()
    m.fs.desal_saturation.properties[0].mole_frac_comp.display()

    # solve for specific saturation
    m.fs.pump_RO.control_volume.properties_out[0].pressure.unfix()
    m.fs.pump_RO.control_volume.properties_out[0].pressure.setlb(20e5)
    m.fs.pump_RO.control_volume.properties_out[0].pressure.setub(120e5)
    m.fs.desal_saturation.saturation_index.fix(1)
    solve_with_user_scaling(m, tee=False, fail_flag=True)
    desalination.display_desalination(m, **kwargs)
    print('Flux:', value(m.fs.RO.flux_mass_phase_comp_avg[0, 'Liq', 'H2O']) * 3600)
    print('Solubility index:', value(m.fs.desal_saturation.saturation_index))

    # optimize LCOW and reach saturation
    # m.fs.pump_RO.display()
    m.fs.objective = Objective(
        expr=((m.fs.RO.area * 30) * 4 * (0.1 + 0.2) + m.fs.pump_RO.control_volume.work[0] / 1000 * 24 * 365 * 0.07))

    m.fs.RO.area.unfix()
    m.fs.RO.area.setlb(10)
    m.fs.RO.area.setub(300)

    solve_with_user_scaling(m, tee=False, fail_flag=True)

    m.fs.RO.area.display()
    m.fs.RO.inlet.display()
    print('Flux:', value(m.fs.RO.flux_mass_phase_comp_avg[0, 'Liq', 'H2O']) * 3600)
    print('Solubility index:', value(m.fs.desal_saturation.saturation_index))

    print('Area costs', (value(m.fs.RO.area) * 30 * (0.1 + 0.2))*2)
    print('Pressure costs', value(m.fs.pump_RO.control_volume.work[0]) / 1000 * 24 * 365 * 0.07)

    return m

if __name__ == "__main__":
    kwargs_flowsheet = {
        'has_bypass': True, 'has_desal_feed': False, 'is_twostage': False,
        'NF_type': 'ZO', 'NF_base': 'ion',
        'RO_type': '0D', 'RO_base': 'TDS', 'RO_level': 'detailed'}
    solve_flowsheet_mvp_NF(**kwargs_flowsheet)
