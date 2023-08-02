#################################################################################
# WaterTAP Copyright (c) 2020-2023, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory, Oak Ridge National Laboratory,
# National Renewable Energy Laboratory, and National Energy Technology
# Laboratory (subject to receipt of any required approvals from the U.S. Dept.
# of Energy). All rights reserved.
#
# Please see the files COPYRIGHT.md and LICENSE.md for full copyright and license
# information, respectively. These files are also available online at the URL
# "https://github.com/watertap-org/watertap/"
#################################################################################
from watertap.tools.parameter_sweep import LinearSample, parameter_sweep
import watertap.examples.flowsheets.case_studies.wastewater_resource_recovery.dye_desalination.dye_desalination as dye_desalination
import watertap.examples.flowsheets.case_studies.wastewater_resource_recovery.dye_desalination.dye_desalination_withRO as dye_desalination_withRO

from pyomo.environ import units as pyunits
import os
from watertap.tools.parameter_sweep.sweep_visualizer import line_plot, contour_plot
import matplotlib.pyplot as plt


def set_up_sensitivity(m, withRO):
    outputs = {}

    # LCOT is an output for both flowsheets
    outputs["LCOT"] = m.fs.LCOT

    # choose the right flowsheet and if ro is enabled add lcow
    if withRO:
        outputs["LCOW"] = m.fs.LCOW
        opt_function = dye_desalination_withRO.solve
    else:
        opt_function = dye_desalination.solve

    optimize_kwargs = {"fail_flag": False}
    return outputs, optimize_kwargs, opt_function


def run_analysis(
    case_num, nx, interpolate_nan_outputs=True, withRO=True, output_filename=None
):

    if output_filename is None:
        output_filename = "sensitivity_" + str(case_num) + ".csv"

    # when from the command line
    case_num = int(case_num)
    nx = int(nx)
    interpolate_nan_outputs = bool(interpolate_nan_outputs)
    withRO = bool(withRO)

    if not withRO and case_num > 7:
        raise ValueError(
            "Case numbers 8 and above are only for dye_desalination_withRO. Please set 'withRO=True'"
        )

    # select flowsheet
    if withRO:
        m = dye_desalination_withRO.main()[0]
    else:
        m = dye_desalination.main()[0]

    # set up sensitivities
    outputs, optimize_kwargs, opt_function = set_up_sensitivity(m, withRO)

    # choose parameter sweep from case structure
    sweep_params = {}

    if case_num == 1:
        m.fs.zo_costing.dye_mass_cost.unfix()
        sweep_params["dye_mass_cost"] = LinearSample(
            m.fs.zo_costing.dye_mass_cost, 0.1, 5, nx
        )

    elif case_num == 2:
        m.fs.zo_costing.waste_disposal_cost.unfix()
        sweep_params["disposal_cost"] = LinearSample(
            m.fs.zo_costing.waste_disposal_cost, 1, 10, nx
        )
    elif case_num == 3:
        m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"].unfix()
        sweep_params["dye_removal"] = LinearSample(
            m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"],
            0.2,
            0.999,
            nx,
        )
    elif case_num == 4:
        # sweep across membrane properties
        m.fs.dye_separation.nanofiltration.water_permeability_coefficient[0].unfix()
        m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"].unfix()
        sweep_params["water_permeability"] = LinearSample(
            m.fs.dye_separation.nanofiltration.water_permeability_coefficient[0],
            50,
            150,
            nx,
        )
        sweep_params["dye_removal"] = LinearSample(
            m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"],
            0.2,
            0.999,
            nx,
        )
    elif case_num == 5:
        # sweep across membrane cost parameters
        m.fs.zo_costing.nanofiltration.membrane_cost.unfix()

        sweep_params["membrane_cost"] = LinearSample(
            m.fs.zo_costing.nanofiltration.membrane_cost, 1, 100, nx
        )
    elif case_num == 6:
        m.fs.zo_costing.dye_mass_cost.unfix()
        m.fs.zo_costing.waste_disposal_cost.unfix()

        sweep_params["dye_cost"] = LinearSample(m.fs.zo_costing.dye_mass_cost, 0, 1, nx)
        sweep_params["waste_disposal"] = LinearSample(
            m.fs.zo_costing.waste_disposal_cost, 0, 10, nx
        )
    elif case_num == 7:
        m.fs.zo_costing.electricity_cost.unfix()
        sweep_params["electricity_cost"] = LinearSample(
            m.fs.zo_costing.electricity_cost, 0.0, 0.25, nx
        )
    elif case_num == 8:
        m.fs.zo_costing.recovered_water_cost.unfix()
        sweep_params["recovered_water_value"] = LinearSample(
            m.fs.zo_costing.recovered_water_cost, 0.0, 1.5, nx
        )
        m.fs.zo_costing.dye_mass_cost.unfix()
        sweep_params["recovered_dye_value"] = LinearSample(
            m.fs.zo_costing.dye_mass_cost, 0.0, 1, nx
        )
    elif case_num == 9:
        m.fs.zo_costing.recovered_water_cost.unfix()
        sweep_params["recovered_water_value"] = LinearSample(
            m.fs.zo_costing.recovered_water_cost, 0.0, 1.5, nx
        )
        m.fs.zo_costing.waste_disposal_cost.unfix()
        sweep_params["waste_disposal_cost"] = LinearSample(
            m.fs.zo_costing.waste_disposal_cost, 0.0, 10, nx
        )
    elif case_num == 10:
        m.fs.zo_costing.electricity_cost.unfix()
        m.fs.zo_costing.recovered_water_cost.unfix()
        sweep_params["recovered_water_value"] = LinearSample(
            m.fs.zo_costing.recovered_water_cost, 0.0, 1.5, nx
        )
        sweep_params["electricity_cost"] = LinearSample(
            m.fs.zo_costing.electricity_cost, 0.0, 0.25, nx
        )
    elif case_num == 11:
        m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"].unfix()
        sweep_params["NF_dye_removal"] = LinearSample(
            m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"],
            0.2,
            1,
            nx,
        )
        m.fs.desalination.RO.A_comp.unfix()
        sweep_params["RO_permeability"] = LinearSample(
            m.fs.desalination.RO.A_comp, 1e-12, 1e-11, nx
        )
    elif case_num == 12:
        desal = m.fs.desalination
        desal.RO.recovery_vol_phase[0, "Liq"].unfix()
        desal.RO.feed_side.velocity[0, 0].unfix()

        desal.P2.control_volume.properties_out[0].pressure.unfix()
        desal.P2.control_volume.properties_out[0].pressure.setub(8300000)
        desal.P2.control_volume.properties_out[0].pressure.setlb(100000)

        desal.RO.area.unfix()
        desal.RO.area.setub(5000)
        desal.RO.area.setlb(50)

        sweep_params["RO_recovery"] = LinearSample(
            m.fs.desalination.RO.recovery_vol_phase[0, "Liq"], 0.1, 0.75, nx
        )
    elif case_num == 13:
        m.fs.feed.conc_mass_comp[0, "dye"].unfix()
        sweep_params["inlet_dye_concentration"] = LinearSample(
            m.fs.feed.conc_mass_comp[0, "dye"], 0.1, 5, nx
        )
        m.fs.feed.conc_mass_comp[0, "tds"].unfix()
        sweep_params["inlet_salt_concentration"] = LinearSample(
            m.fs.feed.conc_mass_comp[0, "tds"], 1, 10, nx
        )
    elif case_num == 14:
        m.fs.dye_separation.P1.eta_pump.unfix()
        sweep_params["pump_efficiency"] = LinearSample(
            m.fs.dye_separation.P1.eta_pump, 0.5, 1, nx
        )
        m.fs.dye_separation.P1.eta_motor.unfix()
        sweep_params["motor_efficiency"] = LinearSample(
            m.fs.dye_separation.P1.eta_motor, 0.5, 1, nx
        )
    elif case_num == 15:
        m.fs.zo_costing.pump_electricity.pump_cost["default"].unfix()
        sweep_params["pump_sizing_cost"] = LinearSample(
            m.fs.zo_costing.pump_electricity.pump_cost["default"], 50, 100, nx
        )
    elif case_num == 16:
        m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"].unfix()
        sweep_params["NF_dye_removal"] = LinearSample(
            m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "dye"],
            0.2,
            1,
            nx,
        )
        m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "tds"].unfix()
        sweep_params["NF_salt_removal"] = LinearSample(
            m.fs.dye_separation.nanofiltration.removal_frac_mass_comp[0, "tds"],
            0.05,
            0.5,
            nx,
        )
    elif case_num == 17:
        m.fs.zo_costing.nanofiltration.membrane_cost["rHGO_dye_rejection"].unfix()
        sweep_params["membrane_cost"] = LinearSample(
            m.fs.zo_costing.nanofiltration.membrane_cost["rHGO_dye_rejection"],
            5,
            75,
            nx,
        )
        m.fs.zo_costing.nanofiltration.membrane_replacement_rate[
            "rHGO_dye_rejection"
        ].unfix()
        sweep_params["membrane_replacement_rate"] = LinearSample(
            m.fs.zo_costing.nanofiltration.membrane_cost["rHGO_dye_rejection"],
            5,
            75,
            nx,
        )

    else:
        raise ValueError("case_num = %d not recognized." % (case_num))

    # run sweep
    global_results = parameter_sweep(
        m,
        sweep_params,
        outputs,
        csv_results_file_name=output_filename,
        optimize_function=opt_function,
        optimize_kwargs=optimize_kwargs,
        interpolate_nan_outputs=interpolate_nan_outputs,
    )

    return global_results, sweep_params, m


def merge_path(filename):
    source_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
    return source_path


def visualize_results(
    case_num,
    plot_type,
    xlabel,
    ylabel,
    xunit=None,
    yunit=None,
    zlabel=None,
    zunit=None,
    levels=None,
    cmap=None,
    isolines=None,
):
    data_file = merge_path("interpolated_sensitivity_" + str(case_num) + ".csv")
    if plot_type == "line":
        fig, ax = line_plot(data_file, xlabel, ylabel, xunit, yunit)

    elif plot_type == "contour":
        fig, ax = contour_plot(
            data_file,
            xlabel,
            ylabel,
            zlabel,
            xunit,
            yunit,
            zunit,
            levels=levels,
            cmap=cmap,
            isolines=isolines,
        )
    else:
        raise ValueError("Plot type not yet implemented")
    return fig, ax


def main(case_num, nx=11, interpolate_nan_outputs=True, withRO=True):
    # when from the command line
    case_num = int(case_num)
    nx = int(nx)
    interpolate_nan_outputs = bool(interpolate_nan_outputs)

    # comm, rank, num_procs = _init_mpi()

    global_results, sweep_params, m = run_analysis(
        case_num, nx, interpolate_nan_outputs, withRO
    )
    # print(global_results)

    # visualize results

    # case 1
    # fig, ax = visualize_results(
    #     case_num,
    #     plot_type="contour",
    #     xlabel="# inlet_dye_concentration",
    #     ylabel="inlet_salt_concentration",
    #     zlabel="LCOW",
    #     isolines=[0],
    #     cmap="GnBu",
    # )
    # ax.plot(0.2, 2, 'ko')
    # ax.set_xlim([0, 5])
    # ax.set_ylim([0, 10])
    # ax.set_xlabel("Inlet Dye Concentration (kg/m3)")
    # ax.set_ylabel("Inlet Salt Concentration (kg/m3)")
    # ax.set_title("LCOW ($/m3)")

    # case 2
    fig, ax = visualize_results(
        case_num,
        plot_type="contour",
        xlabel="# pump_efficiency",
        ylabel="motor_efficiency",
        zlabel="LCOW",
        cmap="GnBu",
    )
    ax.plot(0.75, 0.9, "ko")
    ax.set_xlim([0.5, 1])
    ax.set_ylim([0.5, 1])
    ax.set_xlabel("Pump Efficiency")
    ax.set_ylabel("Motor Efficiency")
    ax.set_title("LCOW ($/m3)")

    # case 3
    # fig, ax = visualize_results(
    #     case_num,
    #     plot_type="contour",
    #     xlabel="# pump_sizing_cost",
    #     ylabel="LCOW",
    #     cmap="GnBu",
    # )
    # ax.set_xlim([0.5, 1])
    # ax.set_xlabel("Pump Sizing Cost")
    # ax.set_ylabel("LCOW")

    # case 4
    # fig, ax = visualize_results(
    #     case_num,
    #     plot_type="contour",
    #     xlabel="# NF_dye_removal",
    #     ylabel="NF_salt_removal",
    #     zlabel="LCOW",
    #     cmap="GnBu",
    # )
    # ax.plot(0.99, 0.05, 'ko')
    # ax.set_xlim([0, 1])
    # ax.set_ylim([0, 1])
    # ax.set_xlabel("Dye Mass Removal Fraction")
    # ax.set_ylabel("Salt Mass Removal Fraction")
    # ax.set_title("LCOW ($/m3)")

    # case 5
    # fig, ax = visualize_results(
    #     case_num,
    #     plot_type="contour",
    #     xlabel="# membrane_cost",
    #     ylabel="membrane_replacement_rate",
    #     zlabel="LCOW",
    #     cmap="GnBu",
    # )
    # ax.plot(50, 0.2, 'ko')
    # ax.set_xlim([10, 100])
    # ax.set_ylim([0.1, 0.5])
    # ax.set_xlabel("Membrane Cost ($/m2) ")
    # ax.set_ylabel("Membrane Replacement Rate per Year")
    # ax.set_title("LCOW ($/m3)")

    return global_results, m


if __name__ == "__main__":
    results, model = main(case_num=14, nx=17)
    # results, sweep_params, m = run_analysis()
