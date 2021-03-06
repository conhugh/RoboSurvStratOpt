# Visualization of the performance of stochastic surveillance strategies
import os
import time
import numpy as np
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
import networkx as nx
import pygraphviz as pgv
import jax.numpy as jnp
import TestSpec as ts
from StratCompJax import *

# Plot transition probabilities for each pair of nodes for the given P matrices
# Takes a list of initial and optimized P matrices
def plot_trans_probs_2D(init_P_mats, opt_P_mats, init_run_nums, opt_run_nums, title, path):
    n = init_P_mats[0].shape[0]
    probs = np.linspace(1, n**2, n**2)
    init_P_mats = np.asarray(init_P_mats)
    opt_P_mats = np.asarray(opt_P_mats)
    init_run_nums = np.asarray(init_run_nums)
    opt_run_nums = np.asarray(opt_run_nums)
    init_sort_inds = np.argsort(init_run_nums)
    opt_sort_inds= np.argsort(opt_run_nums)
    plt.figure()
    ax = plt.gca()
    for k in range(len(init_P_mats)):
        init_P_vec = init_P_mats[init_sort_inds[k]].flatten('F')
        opt_P_vec = opt_P_mats[opt_sort_inds[k]].flatten('F')
        init_num = init_run_nums[init_sort_inds[k]]
        opt_num = opt_run_nums[opt_sort_inds[k]]
        plt.scatter(probs, init_P_vec, marker=".", s=16, color="C" + str(init_num), label="Run " + str(init_num))
        plt.scatter(probs, opt_P_vec, marker=".", s=120, color="C" + str(opt_num))
    plt.xlabel("Pvec Index")
    plt.ylabel("Probability")
    plt.title(title)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.savefig(path, bbox_inches = "tight")
    plt.close()

# Plot transition probabilities for each pair of nodes for the given P matrices,
# averaged across the results of each optimization for varying initial P
# Takes a list of initial and optimized P matrices
def plot_opt_trans_probs_2D(opt_P_mats, folder_path):
    n = opt_P_mats[0].shape[0]
    probs = np.linspace(1, n**2, n**2)
    avg_opt_P_mat = np.mean(opt_P_mats, axis=0)
    stddev_opt_P_mat = np.std(opt_P_mats, axis=0)
    stddevperc_opt_P_mat = 100*np.std(opt_P_mats, axis=0)/(np.mean(opt_P_mats, axis=0) + 0.0000000001)
    avg_opt_P_vec = avg_opt_P_mat.flatten('F')
    stddev_opt_P_vec = stddev_opt_P_mat.flatten('F')
    stddevperc_opt_P_vec = stddevperc_opt_P_mat.flatten('F')
    plt.figure()
    plt.scatter(probs, avg_opt_P_vec, marker=".")
    plt.xlabel("Pvec Index")
    plt.ylabel("Avg Optimized Transition Probability")
    plt.title("Avg Optimized Transition Probabilies")
    plt.savefig(folder_path + "/avgopt_P")
    plt.close()
    plt.figure()
    plt.scatter(probs, stddev_opt_P_vec, marker=".")
    plt.xlabel("Pvec Index")
    plt.ylabel("Std Dev of Optimized Transition Probability")
    plt.title("Std Dev of Optimized Transition Probabilies")
    plt.savefig(folder_path + "/stddevopt_P")
    plt.close()
    plt.figure()
    plt.scatter(probs, stddevperc_opt_P_vec, marker=".")
    plt.xlabel("Pvec Index")
    plt.ylabel("(Std Dev/Avg) of Optimized Transition Probability (%)")
    plt.title("Coefficient of Variation of Optimized Transition Probabilies")
    plt.savefig(folder_path + "/stddevpercopt_P")
    plt.close()

# Plot capture probabilities for each pair of nodes for fixed P matrix
def plot_cap_probs_3D(cap_probs):
    robot_locs = np.arange(cap_probs.shape[0])
    intruder_locs = np.arange(cap_probs.shape[1])
    X, Y = np.meshgrid(robot_locs, intruder_locs)
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.plot_surface(X, Y, cap_probs)
    ax.set_xlabel('Robot Location')
    ax.set_ylabel('Intruder Location')
    ax.set_zlabel('Capture Probability')
    plt.show()

# Plot a function in 3D
# def plot_func_3D(X, Y, func):
#     Z = func(X, Y)
#     robot_locs = np.arange(cap_probs.shape[0])
#     intruder_locs = np.arange(cap_probs.shape[1])
#     X, Y = np.meshgrid(robot_locs, intruder_locs)
#     fig = plt.figure()
#     ax = plt.axes(projection='3d')
#     ax.plot_surface(X, Y, cap_probs)
#     ax.set_xlabel('Robot Location')
#     ax.set_ylabel('Intruder Location')
#     ax.set_zlabel('Capture Probability')
#     plt.show()

# Plot the capture probabilities as a function of P_ij
def comp_CP_var_P(P, tau, i, j, resolution):
    n = P.shape[0]
    cap_probs = jnp.full([n, n, resolution + 1], np.NaN)
    for k in range(resolution + 1):
        # Set the (i, j) element of transition probability matrix:
        P = P.at[i, j].set(k/resolution)
        # Normalize all the other entries in row i to generate valid prob dist:
        rem_row_sum = jnp.sum(P[i, :]) - P[i, j]
        for col in range(jnp.shape(P)[1]):
            if col != j:
                P = P.at[i, col].set(P[i, col]*(1 - P[i, j])/rem_row_sum)
        F0 = jnp.full((n, n, tau), np.NaN)
        cap_probs = cap_probs.at[:, :, k].set(compute_cap_probs(P, F0, tau))
    P_range = jnp.linspace(0, 1, resolution + 1)
    for row in range(jnp.shape(P)[0]):
        for col in range(jnp.shape(P)[1]):
            plt.plot(P_range, cap_probs[row, col, :], label = "(" + str(row) + ", " + str(col) + ")")
    plt.xlabel("P(" + str(i) + ", " + str(j) + ") value")
    plt.ylabel("Capture Probabilities")
    # plt.legend(bbox_to_anchor=(1.05, 0.95), loc='upper right', borderaxespad=-2)
    plt.title("Capture Probabilities for tau = " + str(tau) + " and varying P(" + str(i) + ", " + str(j) + ")")
    plt.savefig(os.getcwd() + "/test_CP_plot.png")
    return cap_probs

# Plot the capture probabilities as a function of P_ij
def comp_MCP_var_P_test(P0, tau, rows, cols, resolution):
    n = P0.shape[0]
    MCPs = jnp.full([resolution + 1], np.NaN)
    for ind in range(len(rows)):
        i = rows[ind]
        j = cols[ind]
        P = P0
        for k in range(resolution + 1):
            # Set the (i, j) element of transition probability matrix:
            P = P.at[i, j].set(k/resolution)
            # Normalize all the other entries in row i to generate valid prob dist:
            rem_row_sum = jnp.sum(P[i, :]) - P[i, j]
            for col in range(jnp.shape(P)[1]):
                if col != j:
                    P = P.at[i, col].set(P[i, col]*(1 - P[i, j])/rem_row_sum)
            F0 = jnp.full((n, n, tau), np.NaN)
            MCPs = MCPs.at[k].set(compute_MCP(P, F0, tau))
        P_range = jnp.linspace(0, 1, resolution + 1)
        plt.plot(P_range, MCPs)
    plt.xlabel("P_ij value")
    plt.ylabel("Capture Probabilities")
    plt.title("Capture Probabilities for tau = " + str(tau) + " and varying P")
    plt.savefig(os.getcwd() + "/test_CP_plot.png")

# Generate a NetworkX graph from adjacency matrix A
def gen_graph(A):
    temp = nx.DiGraph()
    G = nx.from_numpy_matrix(A, create_using=temp)
    return G

# Set the length of all edges in the graph
def set_edge_length(G, A, len):
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if A[i, j] != 0:
                edge = G.get_edge(i, j)
                edge.attr["len"] = len

# Save the environment graph without edge labels:
def draw_env_graph(A, graph_name, folder_path, save=True):
    G = gen_graph(A)
    G_viz = nx.nx_agraph.to_agraph(G)
    set_edge_length(G_viz, A, 2)
    G_viz.graph_attr["nodesep"] = 0.5
    if(save):
        G_viz.layout()
        G_viz.draw(folder_path + "/" + graph_name +  ".png", prog="sfdp")
    return G_viz

# Save the environment graph with edges labeled with transition probabilities:
def draw_trans_prob_graph(A, P, graph_name, folder_path, P_num=None, save=True):
    G_viz = draw_env_graph(A, graph_name, folder_path, save=False)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if A[i, j] == 1:
                e = G_viz.get_edge(i, j)
                e.attr["xlabel"] = "{:.3f}".format(P[i, j])
                e.attr["fontsize"] = 10.0
    if(save):
        # G_viz.write(folder_path + "/" + graph_name + "_P" + str(P_num) + ".dot")
        G_viz.layout()
        G_viz.draw(folder_path + "/" + graph_name + "_P" + str(P_num) +  ".png", prog="sfdp")
    return G_viz

# Save the environment graph with edges labeled with optimized transition probabilities, 
# MCP listed, and node pair corresponding to MCP highlighted:
def draw_opt_graphs(A, opt_P_mats, test_name, opt_P_nums, folder_path):
    n = opt_P_mats[0].shape[0]
    for k in range(len(opt_P_mats)):
        _, _, tau = parse_test_name(test_name)
        # G_viz = draw_trans_prob_graph(A, opt_P_mats[k], test_name, folder_path, opt_P_nums[k], save=False)
        G_viz = draw_avg_opt_graph(A, np.reshape(opt_P_mats[k], (n, n)), int(tau), None, save=False)
        G_viz.layout()
        G_viz.draw(folder_path + "/G_viz_opt_P_" + str(opt_P_nums[k]) +  ".png", prog="sfdp")

# Save the environment graph with edges labeled with average optimized transition probabilities, 
# edge line weights set proportional to trans probs, MCP listed, and node pair corresponding to 
# MCP highlighted:
def draw_avg_opt_graph(A, avg_opt_P_mat, tau, folder_path, save=True):
    G_viz = draw_env_graph(A, None, folder_path, save=False)
    n = jnp.shape(A)[0]
    F0 = jnp.full((n, n, tau), np.NaN)
    F = compute_cap_probs(avg_opt_P_mat, F0, tau)
    MCP = np.min(F)
    MCP_indices = np.where(F == MCP)
    G_viz.graph_attr["labelloc"] = "t"
    G_viz.graph_attr["label"] = "MCP = " + str(MCP) + ", Attack Duration = " + str(tau)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if i in MCP_indices[0]:
                robot_loc = G_viz.get_node(i)
                robot_loc.attr["color"] = "blue"
            if j in MCP_indices[1]:
                intruder_loc = G_viz.get_node(j)
                intruder_loc.attr["color"] = "red"
            if A[i, j] == 1:
                e = G_viz.get_edge(i, j)
                e.attr["xlabel"] = "{:.3f}".format(avg_opt_P_mat[i, j])
                e.attr["fontsize"] = 10.0
                e.attr["penwidth"] = str(10*avg_opt_P_mat[i, j])
                gscale = int(255 - np.around(255*avg_opt_P_mat[i, j]))
                hex_gscale = hex(gscale)
                hex_gscale = hex_gscale[2:]
                if len(hex_gscale) == 1:
                    hex_gscale = "0" + hex_gscale
                e.attr["color"] = "#" + hex_gscale + hex_gscale + hex_gscale
                if avg_opt_P_mat[i, j] == 0:
                    G_viz.delete_edge(i, j)
    if save:
        G_viz.layout()
        G_viz.draw(folder_path + "/G_viz_avg_opt_P.png", prog="sfdp")
    return G_viz

# Plot all capture probabilities corresponding to average optimized Pmat
def plot_CP_avg_opt_P(avg_opt_P_mat, tau, folder_path):
    n = avg_opt_P_mat.shape[0]
    F0 = jnp.full((n, n, tau), np.NaN)
    F = compute_cap_probs(avg_opt_P_mat, F0, tau)
    F_vec = F.flatten('F')
    probs = np.linspace(1, n**2, n**2)
    plt.figure()
    plt.scatter(probs, F_vec, marker=".")
    plt.xlabel("F_vec Index")
    plt.ylabel("Capture Probability")
    plt.title("Capture Probabilities for Avg Optimized Strategy")
    plt.savefig(folder_path + "/avg_opt_Pcap_probs")
    plt.close()

# Parse graph name (test set subdirectory) to get graph number and tau.
# Graph name assumed to be in format: "graphX_tauY", returns X, Y
def parse_test_name(test_name):
    test_num = test_name[(test_name.find("test") + 4):test_name.find("_")]
    tau = test_name[(test_name.find("tau") + 3):len(test_name)]
    graph_name = test_name[test_name.find("_") + 1:test_name.find("_tau")]
    return test_num, graph_name, tau

# Parse metric filename to get run number and metric name.
# Filename assumed to be in format: "[metric_name]_[run_num].csv" (without square brackets).
def parse_metric_name(metric_name):
    metric = metric_name[0:metric_name.find("_")]
    run_num = metric_name[(metric_name.rfind("_") + 1):metric_name.find(".csv")]
    return metric, run_num

# Search through "directory", collecting all files containing data for "metric".
# Return paths to metric data files, as well as corresponding iteration files.
def find_overlay_files(directory, metric):
    iter_filepaths = {}
    metric_filepaths = {}
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        t_metric, t_run_num = parse_metric_name(filename)
        if os.path.isfile(f) and filename.find("iters") != -1:
            iter_filepaths[t_run_num] = f
        if os.path.isfile(f) and (filename.find("iters") == -1):
            if(metric == t_metric):
                metric_filepaths[t_run_num] = f
    return iter_filepaths, metric_filepaths

# Plot optimization metrics as each test completes:
def visualize_metrics(metrics, test_name, test_dir, show_legend=True, overlay=True):
    met_vis_dir = test_dir + "/metrics_visualization"
    if not os.path.isdir(met_vis_dir):
        os.mkdir(met_vis_dir)
    for metric_name in metrics.keys():
        if metric_name.find("final") == -1 and metric_name.find("iters") == -1:
            if overlay:
                plt.figure()
                plt.xlabel("Iteration Number")
                plt.ylabel(metric_name)
                plt.title(test_name)
            for r in range(len(metrics[metric_name])):
                iters = metrics["iters"][r]
                metric_vals = metrics[metric_name][r]
                if not overlay:
                    plt.figure()
                    plt.xlabel("Iteration Number")
                    plt.ylabel(metric_name)
                    plt.title(test_name)
                plt.plot(iters, metric_vals, label="Run " + str(r + 1))
                if not overlay:
                    plot_name = metric_name + "_" + str(r + 1)
                    plt.savefig(os.path.join(met_vis_dir, plot_name), bbox_inches = "tight")
                    plt.close()    
            if overlay:
                if show_legend:
                    ax = plt.gca()
                    box = ax.get_position()
                    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
                plt.savefig(os.path.join(met_vis_dir, metric_name), bbox_inches = "tight")   
                plt.close()

# Visualize metrics related to the optimization process (after all tests have completed):
def visualize_metrics_retro(test_set_name, overlay=False):
    test_set_dir = os.path.join(os.getcwd(), "Results/test_set_" + test_set_name)
    sub_dir_num = len(os.listdir(test_set_dir))
    print("Generating Metrics Visualization...")
    print_progress_bar(0, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for sub_dir_count, sub_dir in enumerate(os.listdir(test_set_dir)):
        if (sub_dir.find("test") != -1 and sub_dir.find("test_spec") == -1):
            test_name = sub_dir
            test_dir = os.path.join(test_set_dir, test_name)
            metrics_dir = os.path.join(test_dir, "metrics")
            met_vis_dir = os.path.join(test_dir, "metrics_visualization")
            if not os.path.isdir(met_vis_dir):
                os.mkdir(met_vis_dir)
            with open(metrics_dir + "/iters.txt") as iters_file:
                iters = []
                line = True
                while line:
                    line = iters_file.readline()
                    line = line.strip()
                    line = line.strip("[]")
                    iters_list = line.split()
                    iters.append(list(map(int, iters_list)))
            for filename in os.listdir(metrics_dir):
                if (filename.find("iters") == -1) and (filename.find("debug") == -1) and (filename.find("final") == -1):
                    metric_file = os.path.join(metrics_dir, filename)
                    metric_name = filename[:filename.find(".")]
                    with open(metric_file) as metric:
                        if overlay:
                            plt.figure()
                            plt.xlabel("Iteration Number")
                            plt.ylabel(metric_name)
                        run_num = 1
                        line = True
                        while line:
                            line = metric.readline()
                            line = line.strip()
                            line = line.strip("[]")
                            metric_string = line.split()
                            metric_vals = list(map(float, metric_string))
                            if not overlay:
                                plt.figure()
                                plt.xlabel("Iteration Number")
                                plt.ylabel(metric_name)
                            plt.plot(iters[run_num - 1], metric_vals, label="Run " + str(run_num))
                            if not overlay:
                                plt.title(test_name + " " + metric_name + " Run " + str(run_num))
                                ax = plt.gca()
                                box = ax.get_position()
                                ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                                plt.legend(loc='upper left', bbox_to_anchor=(1, 1))                            
                                plot_filepath = os.path.join(met_vis_dir, metric_name + "_" + str(run_num))
                                plt.savefig(plot_filepath, bbox_inches = "tight")
                                plt.close()
                            run_num = run_num + 1
                        if overlay:
                            plt.title(test_name + " " + metric_name)
                            ax = plt.gca()
                            box = ax.get_position()
                            ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
                            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))                            
                            plot_filepath = os.path.join(met_vis_dir, metric_name)
                            plt.savefig(plot_filepath, bbox_inches = "tight")
                            plt.close()
        print_progress_bar(sub_dir_count + 1, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)

# Save symmetry-transformed optimized P matrices:
def save_sym_opt_Ps(res_vis_dir, opt_P_mats, opt_P_run_nums):
    for i in range(len(opt_P_run_nums)):
        np.savetxt(res_vis_dir + "/sym_transformed_opt_P_" + str(opt_P_run_nums[i]) + ".csv", opt_P_mats[i], delimiter=',')

# Visualize initial and optimized P matrices: 
def visualize_results(test_set_name, num_top_MCP_runs=None):
    test_set_dir = os.path.join(os.getcwd(), "Results/test_set_" + test_set_name)
    sub_dir_num = len(os.listdir(test_set_dir))
    print("Generating Results Visualization...")
    print_progress_bar(0, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for sub_dir_count, sub_dir in enumerate(os.listdir(test_set_dir)):
        if(sub_dir.find("test") != -1 and sub_dir.find("test_spec") == -1):
            test_name = sub_dir
            _, graph_name, tau = parse_test_name(test_name)
            test_dir = os.path.join(test_set_dir, test_name)
            res_dir = os.path.join(test_dir, "results")
            metrics_dir = os.path.join(test_dir, "metrics")
            res_vis_dir = os.path.join(test_dir, "results_visualization")
            if not os.path.isdir(res_vis_dir):
                os.mkdir(res_vis_dir)
            with open(test_dir + "/A.csv") as A:
                A = np.loadtxt(A, delimiter = ',')
            top_MCP_run_nums=None
            if num_top_MCP_runs is not None:
                final_MCP_path = os.path.join(metrics_dir, "final_MCP.txt")
                with open(final_MCP_path) as final_MCP_file:
                    final_MCPs = np.loadtxt(final_MCP_file)
                    top_MCP_run_nums = np.argsort(final_MCPs)[len(final_MCPs) - num_top_MCP_runs:] + 1
            init_P_mats = [] 
            opt_P_mats = []
            init_run_nums = []
            opt_run_nums = []
            for filename in os.listdir(res_dir):
                run_num = int(filename[filename.rfind("_") + 1:filename.find(".csv")])
                if top_MCP_run_nums is None or run_num in top_MCP_run_nums:
                    f = os.path.join(res_dir, filename)
                    if(filename.find("init_P") != -1):
                        with open(f) as init_P:
                            init_P = np.loadtxt(init_P, delimiter = ',')
                            init_P_mats.append(init_P)
                            init_run_nums.append(run_num)
                    if(filename.find("opt_P") != -1):
                        with open(f) as opt_P:
                            opt_P = np.loadtxt(opt_P, delimiter = ',')
                            opt_P_mats.append(opt_P)
                            opt_run_nums.append(run_num)
            if graph_name.find("grid") != -1:
                gridw = int(graph_name[graph_name.find("_W") + 2:graph_name.find("_H")])
                gridh = int(graph_name[graph_name.find("_H") + 2:])
                P_ref = opt_P_mats[0]
                for r in range(1, len(opt_P_mats)):
                    opt_P_mats[r], sym_ind = get_closest_sym_strat_grid(P_ref, opt_P_mats[r], gridh, gridw)
                    init_P_mats[r], _ = get_closest_sym_strat_grid(P_ref, opt_P_mats[r], gridh, gridw, sym_ind)
            save_sym_opt_Ps(res_vis_dir, opt_P_mats, opt_run_nums)
            plot_trans_probs_2D(init_P_mats, opt_P_mats, init_run_nums, opt_run_nums, \
                                test_name, os.path.join(res_vis_dir, "P_plot2D")) 
            plot_opt_trans_probs_2D(opt_P_mats, res_vis_dir)
            avg_opt_P_mat = np.mean(opt_P_mats, axis=0)
            draw_avg_opt_graph(A, avg_opt_P_mat, int(tau), res_vis_dir)
            plot_CP_avg_opt_P(avg_opt_P_mat, int(tau), res_vis_dir)
            draw_opt_graphs(A, opt_P_mats, test_name, opt_run_nums, res_vis_dir)
        print_progress_bar(sub_dir_count + 1, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)

def visualize_MCPs(test_set_name, tau_study=True, num_top_MCPs=None, plot_best_fit=False):
    test_set_dir = os.path.join(os.getcwd(), "Results/test_set_" + test_set_name)
    MCP_dir = os.path.join(test_set_dir, "MCP_results")
    if not os.path.isdir(MCP_dir):
        os.mkdir(MCP_dir)
    MCP_data = get_MCP_data(test_set_name, num_top_MCPs)
    plt.figure()
    if tau_study:
        plt.scatter(MCP_data["taus"], MCP_data["MCP_avgs"])
        plt.xlabel("Tau")
        if plot_best_fit:
            m, b = np.polyfit(MCP_data["taus"], MCP_data["MCP_avgs"], 1)
            plt.plot(MCP_data["taus"], m*MCP_data["taus"] + b, label="LSQ Fit: MCP = " + str(m)[:5] + "*tau + " + str(b)[:5] )
            ax = plt.gca()
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    else:
        plt.scatter(MCP_data["test_nums"], MCP_data["MCP_avgs"]) #, label="Graph: " + graph_name + ", Tau: " + tau)
        plt.xlabel("Test Number")
        ax = plt.gca()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.ylabel("Average Optimized MCP")

    if num_top_MCPs is not None:
        plt.title("Averages of Top " + str(num_top_MCPs) + " MCPs")
        plt.savefig(MCP_dir + "/avg_top" + str(num_top_MCPs) + "_MCPs",  bbox_inches = "tight")
    else:
        plt.title("Averages of Optimized MCP")
        plt.savefig(MCP_dir + "/avgMCPs",  bbox_inches = "tight")
    plt.close()
    plt.figure()
    if tau_study:
        plt.xlabel("Tau")
        for r in range(MCP_data["final_MCP_taus"].shape[1]):
            plt.scatter(MCP_data["final_MCP_taus"][:, r], MCP_data["final_MCPs"][:, r], marker=".", s=30, color="C" + str(r + 1))
        if plot_best_fit:
            m, b = np.polyfit(MCP_data["final_MCP_taus"].flatten(), MCP_data["final_MCPs"].flatten(), 1)
            plt.plot(MCP_data["taus"], m*MCP_data["taus"] + b, label="LSQ Fit: MCP = " + str(m)[:5] + "*tau + " + str(b)[:5])
            ax = plt.gca()
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    else:
        plt.xlabel("Test Number")
        for r in range(MCP_data["final_MCP_test_nums"].shape[1]):
            plt.scatter(MCP_data["final_MCP_test_nums"][:, r], MCP_data["final_MCPs"][:, r], marker=".", s=30, color="C" + str(r + 1))
    plt.ylabel("Optimized MCPs")
    if num_top_MCPs is not None:
        plt.title("Top " + str(num_top_MCPs) + " Optimized MCPs")
        plt.savefig(MCP_dir + "/top" + str(num_top_MCPs) + "_MCPs",  bbox_inches = "tight")
    else:
        plt.title("Optimized MCPs")
        plt.savefig(MCP_dir + "/MCPs",  bbox_inches = "tight")
    plt.close()
    plt.figure()
    if tau_study:
        plt.xlabel("Tau")
        plt.scatter(MCP_data["taus"], MCP_data["MCP_stddevs"])
    else:
        plt.xlabel("Test Number")
        plt.scatter(MCP_data["test_nums"], MCP_data["MCP_stddevs"]) #, label="Graph: " + graph_name + ", Tau: " + tau)
        ax = plt.gca()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.ylabel("Std Deviation of Optimized MCPs")
    if num_top_MCPs is not None:
        plt.title("Std Deviation of Top " + str(num_top_MCPs) + " MCPs")
        plt.savefig(MCP_dir + "/stddev_top" + str(num_top_MCPs) + "_MCPs",  bbox_inches = "tight")
    else:
        plt.title("Std Deviation of Optimized MCPs")
        plt.savefig(MCP_dir + "/stddevMCPs", bbox_inches = "tight")
    plt.close()
    plt.figure()
    if tau_study:
        plt.xlabel("Tau")
        plt.scatter(MCP_data["taus"], MCP_data["MCP_stddevpercents"])
    else:
        plt.xlabel("Test Number")
        plt.scatter(MCP_data["test_nums"], MCP_data["MCP_stddevpercents"]) #, label="Graph: " + graph_name + ", Tau: " + tau)
        ax = plt.gca()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.ylabel("(Std Deviation/Avg) of Optimized MCPs (%)")
    if num_top_MCPs is not None:
        plt.title("Coefficient of Variation of Top " + str(num_top_MCPs) + " MCPs")
        plt.savefig(MCP_dir + "/stddevperc_top" + str(num_top_MCPs) + "_MCPs",  bbox_inches = "tight")
    else:
        plt.title("Coefficient of Variation of Optimized MCPs")
        plt.savefig(MCP_dir + "/stddevpercMCPs",  bbox_inches = "tight")
    plt.close()

def get_MCP_data(test_set_name, num_top_MCPs=None):
    test_set_dir = os.path.join(os.getcwd(), "Results/test_set_" + test_set_name)
    MCP_dir = os.path.join(test_set_dir, "MCP_results")
    if not os.path.isdir(MCP_dir):
        os.mkdir(MCP_dir)
    MCP_data = {
        "test_nums": [],
        "graph_names": [],
        "taus": [],
        "final_MCPs": [],
        "final_MCP_test_nums": [],
        "final_MCP_taus": [],
        "MCP_avgs": [],
        "MCP_stddevs": [],
        "MCP_stddevpercents": []
    }
    sub_dir_num = len(os.listdir(test_set_dir))
    print("Generating MCP visualization...")
    print_progress_bar(0, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for sub_dir_count, sub_dir in enumerate(os.listdir(test_set_dir)):
        if(sub_dir.find("test") != -1 and sub_dir.find("test_spec") == -1):
            test_name = sub_dir
            test_num, graph_name, tau = parse_test_name(test_name)
            MCP_data["test_nums"].append(test_num)
            MCP_data["graph_names"].append(graph_name)
            MCP_data["taus"].append(tau)
            test_dir = os.path.join(test_set_dir, test_name)
            info_filepath = os.path.join(test_dir, "test" + str(test_num) + "_info.txt")
            with open(info_filepath) as info:
                line = True
                while line:
                    line = info.readline()
                    if(line.find("Final MCPs achieved") != -1):
                        MCP_string = line.strip("[]")
                        # MCP_string = line[line.find("[") + 1:line.find("]")]
                        MCPs = MCP_string.split()
                        MCPs = list(map(float, MCPs))
                        if num_top_MCPs is not None:
                            MCPs.sort(reverse=True)
                            MCPs = MCPs[:int(num_top_MCPs)]
                        MCP_data["final_MCPs"].append(MCPs)
                        MCP_data["final_MCP_test_nums"].append(np.full(len(MCPs), test_num))
                        MCP_data["final_MCP_taus"].append(np.full(len(MCPs), tau))
                        MCP_data["MCP_avgs"].append(np.mean(MCPs))
                        MCP_data["MCP_stddevs"].append(np.std(MCPs))
                        MCP_data["MCP_stddevpercents"].append(100*(np.std(MCPs)/np.mean(MCPs)))
        print_progress_bar(sub_dir_count + 1, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)
    MCP_data["test_nums"] = np.asarray(list(map(int, MCP_data["test_nums"])))
    MCP_data["taus"] = np.asarray(list(map(float, MCP_data["taus"])))
    MCP_data["final_MCP_test_nums"] = np.asarray(MCP_data["final_MCP_test_nums"], dtype=int)
    MCP_data["final_MCPs"] = np.asarray(MCP_data["final_MCPs"])
    MCP_data["final_MCP_taus"] = np.asarray(MCP_data["final_MCP_taus"], dtype=float)
    return MCP_data

# Plot runtimes vs MCPs for each optimizer (inline with optimization):
def plot_optimizer_comparison(test_set_dir, test_spec, run_times, final_iters, final_MCPs):
    avg_run_times = []
    avg_iters = []
    avg_MCPs = []
    for i in range(len(final_MCPs)):
        MCPs = np.asarray(final_MCPs[i])
        max_MCP_inds = np.argsort(MCPs)[len(MCPs) - 3:]
        avg_MCPs.append(np.mean(MCPs[max_MCP_inds]))
        iters = np.asarray(final_iters[i])
        avg_iters.append(np.mean(iters[max_MCP_inds]))
        times = np.asarray(run_times[i])
        avg_run_times.append(np.mean(times[max_MCP_inds]))

    plt.figure()
    ax = plt.gca()
    for i in range(test_spec.num_tests):
        optimizer_name = test_spec.optimizer_params["test" + str(i + 1)]["optimizer_name"]
        plt.scatter(avg_run_times[i], avg_MCPs[i], marker=".", s=120, \
            label="Test" + str(i + 1) + ", Optimizer: " + optimizer_name)
    plt.xlabel("Avg Run Time (seconds)")
    plt.ylabel("Avg Final MCP")
    plt.title("Avg MCPs vs Run Times for 3 Highest-MCP Runs")
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.savefig(test_set_dir + "/OptimizerComparison.png", bbox_inches = "tight")
    plt.close()

# Plot runtimes vs MCPs for each optimizer (after optimization has completed):
def plot_optimizer_comparison_retro(test_set_name):
    avg_run_times = []
    avg_iters = []
    avg_MCPs = []
    test_nums = []
    test_set_dir = os.path.join(os.getcwd(), "Results/test_set_" + test_set_name)
    test_spec = ts.TestSpec(test_spec_filepath=test_set_dir + "/test_spec.json")
    sub_dir_num = len(os.listdir(test_set_dir))
    print("Generating Optimizer Comparison Visualization...")
    print_progress_bar(0, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)
    for sub_dir_count, sub_dir in enumerate(os.listdir(test_set_dir)):
        if(sub_dir.find("test") != -1 and sub_dir.find("test_spec") == -1):
            test_name = sub_dir
            test_num, _, _ = parse_test_name(test_name)
            test_dir = os.path.join(test_set_dir, test_name)
            with open(test_dir + "/test" + str(test_num) + "_info.txt") as info:
                line = True
                while line:
                    line = info.readline()
                    if(line.lower().find("final mcps achieved") != -1):
                        MCP_string = line[line.find("[") + 1:line.find("]")]
                        if MCP_string.find(",") != -1:
                            MCPs = MCP_string.split(",")
                        else:
                            MCPs = MCP_string.split()
                        MCPs = np.asarray(list(map(float, MCPs)))
                    if(line.lower().find("iterations required") != -1):
                        iter_string = line[line.find("[") + 1:line.find("]")]
                        if iter_string.find(",") != -1:
                            iters = iter_string.split(",")
                        else:
                            iters = iter_string.split()
                        iters = np.asarray(list(map(int, iters)))
                    if(line.lower().find("times required") != -1):
                        times_string = line[line.find("[") + 1:line.find("]")]
                        if  times_string.find(",") != -1:
                            run_times =  times_string.split(",")
                        else:
                            run_times = times_string.split()
                        run_times = np.asarray(list(map(float, run_times)))
            test_nums.append(test_num)
            max_MCP_inds = np.argsort(MCPs)[len(MCPs) - 3:]
            avg_MCPs.append(np.mean(MCPs[max_MCP_inds]))
            avg_iters.append(np.mean(iters[max_MCP_inds]))
            avg_run_times.append(np.mean(run_times[max_MCP_inds]))
        print_progress_bar(sub_dir_count + 1, sub_dir_num, prefix = 'Progress:', suffix = 'Complete', length = 50)

    test_nums = np.asarray(test_nums)
    test_inds = np.argsort(test_nums)
    plt.figure()
    ax = plt.gca()
    for i in range(test_spec.num_tests):
        optimizer_name = test_spec.optimizer_params["test" + str(i + 1)]["optimizer_name"]
        plt.scatter(avg_run_times[test_inds[i]], avg_MCPs[test_inds[i]], marker=".", s=120, \
            label="Test" + str(test_nums[test_inds[i]]) + ", Optimizer: " + optimizer_name)
    plt.xlabel("Avg Run Time (seconds)")
    plt.ylabel("Avg Final MCP")
    plt.title("Avg MCPs vs Run Times for 3 Highest-MCP Runs")
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.savefig(test_set_dir + "/OptimizerComparison.png", bbox_inches = "tight")
    plt.close()

# Print iterations progress
def print_progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '???', print_end = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = print_end)
    # Print New Line on Complete
    if iteration == total: 
        print()
    
            
# TESTING -------------------------------------------------------------------------------------------------
if __name__ == '__main__':


    # A, graph_name = gen_star_G(6)
    # tau = 2
    # initQ = jnp.ones(jnp.shape(A))    
    # initP = comp_P_param(initQ, A)
    # # initP = np.asarray(initP)
    # rows = [0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5]
    # cols = [0, 1, 2, 3, 4, 5, 0, 0, 0, 0, 0, 0]
    # # rows = [0, 0]
    # # cols = [0, 1]
    # comp_MCP_var_P_test(initP, tau, rows, cols, 50)

    # test_set_name = "InitP100_Study_D3RandTree1"
    # visualize_results(test_set_name, num_top_MCP_runs=5)

    for i in range(10):
        A, graph_name = gen_rand_tree_G(12, 3)
        print(graph_name)
        draw_env_graph(A, graph_name + "_" + str(i), os.getcwd())
        # print(A)

    # visualize_metrics_retro(test_set_name, overlay=True)
    # visualize_results(test_set_name, num_top_MCP_runs=5)
    # visualize_MCPs(test_set_name, tau_study=True, num_top_MCPs=None, plot_best_fit=True)
    # visualize_MCPs(test_set_name, tau_study=True, num_top_MCPs=1, plot_best_fit=True)
    # visualize_MCPs(test_set_name, tau_study=True, num_top_MCPs=5, plot_best_fit=True)
    # visualize_MCPs(test_set_name, tau_study=True, num_top_MCPs=10, plot_best_fit=True)
    # plot_optimizer_comparison_retro(test_set_name)

    # import_testing()

    # gscale = int(np.around(255*0.01))
    # hex_gscale = hex(gscale)
    # print(hex_gscale)

    # x = np.array([1, 2, 3, 0, 4])
    # print(len(x))
    # x_inds = np.argsort(x)
    # print(x_inds)
    # print(x_inds[len(x) - 2:])
    # y = np.array([[0, 0, 0], [1, 2, 1], [2, 4, 1], [3, 6, 0]])
    # print(y.shape)

    # plt.figure()
    # plt.plot(x, y)
    # plt.savefig("testfig", bbox_inches = "tight")


    # P = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])  # initialize transition prob matrix
    # # P = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]])  # initialize transition prob matrix
    # P = np.matmul(np.diag(1/np.sum(P, axis=1)), P)   # normalize to generate valid prob dist

    # tau = 2  # attack duration

    # plot_cap_probs_3D(cap_probs)

    # cap_probs = comp_CP_var_P(P, 3, 0, 0)

    # # A = gen_star_G(9)
    # A = np.array([[1, 0, 1, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0], [0, 0, 1, 1, 1, 1, 1], [0, 0, 0, 1, 1, 0, 0], [0, 0, 0, 1, 0, 1, 0], [0, 0, 0, 1, 0, 0, 1]])
    # # print(A)
    # # P0 = np.array([[0, 0.2, 1 - 0.2], [1, 0, 0], [1, 0, 0]])
    # P0 = initRandP(A)

    # # fig2 = plt.figure()
    # # ax2 = plt.plot()
    # G = gen_graph(A)
    # # nx.draw(G, with_labels=True, font_weight='bold')
    # # plt.show()

    # G_viz = nx.nx_agraph.to_agraph(G)

    # center = G_viz.get_node(0)
    # center.attr["color"] = "blue"
    # # center.attr["fixedsize"] = True
    # # center.attr["imagescale"] = True
    # # center.attr["image"] = "small robot.png"

    # # intruder_loc = G_viz.get_node(3)
    # # intruder_loc.attr["color"] = "red"
    # # intruder_loc.attr["fixedsize"] = True
    # # intruder_loc.attr["image"] = "small intruder.png"

    # for i in range(A.shape[0]):
    #     for j in range(A.shape[1]):
    #         if A[i, j] == 1:
    #             e = G_viz.get_edge(i, j)
    #             e.attr["xlabel"] = "{:.3f}".format(P0[i, j])
    #             # e.attr["decorate"] = True
    #             # e.attr["labelfloat"] = True
    #             e.attr["fontsize"] = 10.0

    # # e = G_viz.get_edge(center, intruder_loc)
    # # e.attr["label"] = "P_03"
    # # e.attr["color"] = "blue"

    # set_edge_length(G_viz, A, 2)

    # G_viz.graph_attr["nodesep"] = 0.5
    # G_viz.graph_attr["len"] = 4
    # G_viz.write("test_graph.dot")
    # G_viz.layout()
    # G_viz.draw("test_graph.png", prog="sfdp")
    # # G_viz.draw("test_graph.png", prog="neato")