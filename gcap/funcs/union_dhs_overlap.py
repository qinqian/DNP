#########################################################
#
# union DHS evaluation
# add cutting bias borrowed from Tarela
#
#########################################################
from samflow.command import ShellCommand, PythonCommand
from samflow.workflow import Workflow, attach_back
from gcap.funcs.helpers import *
from pkg_resources import resource_filename

def union_DHS_overlap(workflow, conf, tex):
    """ use hotspot d narrow peaks for DHS evaluation """
    for i, target in enumerate(conf.treatment_targets):
        if conf.peakcalltool == "hotspot":
            peaks = conf.hotspot_reps_final_5M_prefix[i] + ".fdr0.01.pks.bed"
            output = target + "_DHS_overlap_peaks_bed"
        elif conf.peakcalltool == "macs2":
            peaks = target + "_5M_macs2_velcro_non_overlap_peaks.bed.final"
            output = target + "_macs2_DHS_overlap_peaks_bed"

        attach_back(workflow,
            ShellCommand(
                "{tool} -wa -u  \
                -a {input[pks_spot_bed]} -b {input[DHS_peaks_bed]} > {output}",
                tool="intersectBed",
                input={"pks_spot_bed": peaks,
                       "DHS_peaks_bed": conf.get("lib", "dhs")},
                output = output,
                name = "Write out DHS overlap BED"))

        ## for hotspot only now, support BED files, not fully tested
        if conf.get("cut_bias", "run").strip().upper() == "T":
            if "bed" in conf.seq_type:
                cut = attach_back(workflow,
                    ShellCommand(
                        "{tool} {param[script]} -p {input[peaks]} -s {input[bit]} -o {output[matrix]} -f {param[mer]} -t {input[tag]}",
                        tool = "python2.7",
                        input = {"peaks": conf.get("lib", "dhs"), "bit": conf.get("cut_bias", "seq_2bit"),
                                 "tag": target + "_all.bed"},
                        output = {"matrix": conf.treatment_targets[i] + "_cut_bias.xls"},
                        param = {"mer": 3, "script": resource_filename("gcap", "pipeline-scripts/twobit_seqbias.py")},
                        name = "cutting bias"))
                cut.update(param = conf.items("cut_bias"))
            else:
                cut = attach_back(workflow,
                    ShellCommand(
                        "bamToBed -i {input[tag]} > {output[tag]} && {tool} {param[script]} -p {input[peaks]} -s {input[bit]} -o {output[matrix]} -f {param[mer]} -t {output[tag]}",
                        tool = "python2.7",
                        input = {"peaks": conf.get("lib", "dhs"), "bit": conf.get("cut_bias", "seq_2bit"),
                                 "tag": target + ".bam"},
                        output = {"tag": target + "_cut_input.bed", "matrix": conf.treatment_targets[i] + "_cut_bias.xls"},
                        param = {"mer": 3, "script": resource_filename("gcap", "pipeline-scripts/twobit_seqbias.py")},
                        name = "cutting bias"))
                cut.update(param = conf.items("cut_bias"))


    attach_back(workflow, PythonCommand(
        stat_dhs,
        input={"dhs_peaks": [ target + "_DHS_overlap_peaks_bed" if conf.peakcalltool == "hotspot" else target + "_macs2_DHS_overlap_peaks_bed"
                              for target in conf.treatment_targets ],
               "pks_spot_bed": [ conf.hotspot_reps_final_5M_prefix[i] + ".fdr0.01.pks.bed" if conf.peakcalltool == "hotspot" else target + "_5M_macs2_velcro_non_overlap_peaks.bed.final"
                                 for i, target in enumerate(conf.treatment_targets) ]},
        output = {"json": conf.json_prefix + "_dhs.json"},
        param= {"samples":conf.treatment_bases},
        name="DHS summary"))
    attach_back(workflow, PythonCommand(
        DHS_doc,
        input = {"tex": tex, "json": conf.json_prefix + "_dhs.json"},
        output = {"latex": conf.latex_prefix + "_dhs.tex"},
        param = {"reps": len(conf.treatment_pairs), "samples": conf.treatment_bases}))


def stat_dhs(input={"pks_spot_bed": "", "dhs_peaks": ""}, output={"json": ""},
             param={"samples": ""}):
    """
    overlap with union DHS
    """
    peaks_info = {}
    for b, d, s in zip(input["pks_spot_bed"], input["dhs_peaks"], param["samples"]):
        print(b, d, s)

        peaks_info[s] = {}
        peaks_info[s]["total"] = len(open(b, 'r').readlines())
        peaks_info[s]["dhs"] = len(open(d, 'r').readlines())
        peaks_info[s]['dhspercentage'] = peaks_info[s]["dhs"] / peaks_info[s]["total"]
    json_dict = {"stat": {}, "input": input, "output": output, "param": param}
    json_dict["stat"] = peaks_info
    json_dump(json_dict)

def DHS_doc(input = {"json": "", "tex": ""}, output = {"latex": ""}, param = {"reps": "", "samples": ""}):
    data = json_load(input["json"])["stat"]
    dhs = []

    for s in param["samples"]:
        dhs.append(decimal_to_latex_percent(data[s]["dhspercentage"]))

    DHS_latex = JinjaTemplateCommand(
        template = input["tex"],
        name = "DHS",
        param = {"section_name": "DHS",
                 "render_dump": output["latex"],
                 "DHS": dhs,
                 "reps": param["reps"]})
    template_dump(DHS_latex)