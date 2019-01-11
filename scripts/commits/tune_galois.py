import os
import difflib
import subprocess
import datetime
import argparse

thread_no = 56;
no_iter   = 3;
get_src_from_file = 0;

#app_lists   = ["pr", "cc", "sssp", "bfs"]
#app_lists = ["sssp", "bfs"]
file_lists  = { "bfs":{"dir":"bfs", "src":"bfs"}, \
		"cc":{"dir":"connectedcomponents", "src":"ConnectedComponents"}, \
		"pr":{"dir":"pagerank", "src":"PageRank-pull"}, \
		"sssp":{"dir":"sssp", "src":"SSSP"} };
#app_lists  = [ "cc" ]

# possible algorithm options per application
app_algorithms = {"bfs":["AsyncTile", "Async", "SyncTile", "Sync", "Sync2pTile","Sync2p"],
                 "sssp":["deltaTile", "deltaStep", "serDeltaTile", "serDelta", "dijkstraTile",
                 "dijkstra", "topo", "topoTile"],
                 "cc":["Async", "EdgeAsync", "EdgetiledAsync", "BlockedAsync", "LabelProp", 
                 "Serial", "Sync"],
                 "pr":["Residual"],
                 "prb":["Residual"] # pagerank with bitmap frontier data structure};

#app_algorithms = {"bfs":["Sync"], "sssp":["deltaStep"]};
#app_algorithms = {"cc":["Async", "LabelProp"]}
#graphs = ["road-usad", "friendster", "socLive", "twitter", "webGraph"];

# directories
src_dir      = "/h1/hlee/far_hlee/workspace/LocalGalois/lonestar/"
base_dir     = "/h1/hlee/far_hlee/workspace/LocalGalois/"
# input graphs directory
input_dir    = base_dir+"/paper_inputs/";
#output_dir   = base_dir+"/paper_outputs/galois_tune/";
output_dir   = base_dir+"/paper_outputs/pr_cmp_prb";
# binary directory
bin_dir      = base_dir+"bin/";

# summarize dictionary which maintains min latencies consumed by and algorithm used by 
# each algorithm
# to sum up, the first key is graph, and the second key is application name
# and the last item is tuple of latencies and algorithm name used by the experiments
best_dat      = {};

def get_starting_points(graph):
    """ Use the points with non-zero out degree and don't hang during execution.  """
    if graph != "friendster":
        return ["17", "38", "47", "52", "53", "58", "59", "69", "94", "96"]
    else:
        # friendster takes a long time so use fewer starting points
        return ["101", "286", "16966", "37728", "56030", "155929"]


def get_starting_points_from_file(app, graph):
    """ read a start point from a file.
    In general, the start point has the maximum degree. """
    if app != "pr" or app != "prb":
        _fname = graph+".gr.source";
    else:
        # page rank takes a transposed graph. 
        _fname = graph+".tgr.source";
    _fdir  = input_dir+_fname;
    if not os.path.isfile(_fdir):
        print("the directory does not exist: \n"+_fdir);
    _fp    = open(_fdir, "r");
    _snode = _fp.readline().rstrip();
    _fp.close();
    _slist = [];  _slist.append(_snode);
    return _slist;

def get_cmd_galois(g, p, point, bin_dir, sel_algo, thread_no):
    if (g in ["netflix", "netflix_2x"] and p != "cf"):
        return ""
    if (g not in ["netflix", "netflix_2x"] and p == "cf"):
        return ""

    if (p == "pr" or p == "prb"):
        graph_path = input_dir + g + "_galois.tgr"
    elif (p == "bfs"):
        graph_path = input_dir + g + "-nw_galois.gr"
    elif (p == "cc"):
        graph_path = input_dir + g + "_galois.csgr"
    else:
        graph_path = input_dir + g + "_galois.gr"

    args = graph_path
    if (p == "cc"):
        # This statement will be removed.
        # Graph-it used directed graphs to get results.
        # However, Galois cannot accept the directed graphs for CC.
        # Therefore, verification of Galois would not work for them.
        #args += " -t="+str(thread_no)+" -noverify "
        args += " -t="+str(thread_no)+" "
    else:
        args += " -t="+str(thread_no)+" "
    if not p == "pr" and not p == "prb":
    	args += "-algo="+sel_algo+" "
 
    if p == "sssp" or p == "bfs":
        args += " -startNode=" + str(point)
    elif p == "pr" or p == "prb":
    #    args += " -maxIterations=21 -algo=Residual "
        args += " -algo=Residual "
    command = bin_dir + " " + args;
    return command;


def get_cmd(framework, graph, app, point, bin_dir, sel_algo, th_no):
    if framework == "galois":
        cmd = get_cmd_galois(graph, app, point, bin_dir, sel_algo, th_no);
    return cmd;

def execute(framework, graph, app, snode, bin_dir, sel_algo, th_no):
    # consturct a command.
    cmd = get_cmd(framework, graph, app, snode, bin_dir, sel_algo, th_no);
    print(cmd);
    out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = out.communicate()
    return output

def get_bin_fname(app): 
    # simply get binary file name.
    if app == "pr":
        return "pagerank-pull"
    elif app == "prb":
        return "pagerank-pull-bmap"
    elif app == "cc":
        return "connectedcomponents"
    return app;

def attach_summ_begin(_fdir, n_line):
    _fp     = open(_fdir, "r");
    a_lines = _fp.readlines();
    a_lines.insert(0, n_line);
    _fp.close();
    _fp     = open(_fdir, "w");
    _fp.writelines(a_lines);
    _fp.close();
            
def summarize_best_dat(_fdir, _dic, app_lists, graph_lists):
    """ The best result that in this experiment, has the smallest latencies
        is summarized in beginning of the result files. """
    nl_line = ',';
    # write application name
    for _a in app_lists:
        nl_line += _a + ",";
    nl_line += "\n";
    # write a row which is for graph name + latency
    for _i_g in graph_lists:
        nl_line += _i_g + ",";
        for _a in app_lists:
            nl_line += str(format(_dic[_i_g][_a][0], 'f'))+",";
        nl_line += '\n';
    nl_line += ','
    for _a in app_lists:
        nl_line += _a + ",";
    nl_line += "\n";
    for _i_g in graph_lists:
        nl_line += _i_g + ",";
        for _a in app_lists:
            nl_line += str(_dic[_i_g][_a][1])+",";
        nl_line += '\n';
    attach_summ_begin(_fdir, nl_line);
    

def main():
    # parsing arguments and setting configurations
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-g', '--graphs', nargs='+',
            default=["socLive", "twitter", "road-usad",
                                "webGraph", "friendster"],
            help="enable graphs with socLive, twitter, \
            road-usad, webGraph and friendster. Defaults to all \
            listed graphs.")
    parser.add_argument('-a', '--applications', nargs='+',
            default=["bfs", "sssp", "pr", "cc"],
            help="applications to benchmark. \
                Defaults to all applications.")
    parser.add_argument('-t', '--threads',
            default=56,
            help="the number of threads. Default is 56", type=int)
    parser.add_argument('-i', '--iteration',
            default="1", type=int,
            help="the number of iterations for the experiments. \
                Default is 1.")
    parser.add_argument('-s', '--snodeFrom',
            default=0, type=int,
            help="Setting start nodes for BFS and SSSP. \
            You can get start from .source files (1) or use \
            default snode lists on the script (0). \
            Default is using default snode lists on the script (0).")

    args = parser.parse_args()

    # running experiments
    summary_fp = open(output_dir+"/summary", "w");
    log_fp     = open(output_dir+"/log", "w");
    for input_graph in args.graphs:
        best_dat[input_graph] = {};
        for app in args.applications:
            best_dat[input_graph][app]=[];
            best_dat[input_graph][app].append(99999999999);
            best_dat[input_graph][app].append(99999999999);

            # setup start nodes for bfs and sssp.
            if app == "bfs" or app == "sssp":
                if args.snodeFrom == 1:
                    spoints = get_starting_points_from_file(app, input_graph);
                else:
                    spoints = get_starting_points(input_graph);
            # TODO: others do not need a start point.
            else:
                spoints = ["1"];

            exec_bin_dir = bin_dir+"/"+get_bin_fname(app);
            summary_fp.write("Application: "+app+", Input Graph: "+input_graph+",\n");
            for sel_algo in app_algorithms[app]:
                print("app:"+app+", input_g:"+input_graph+", algo:"+sel_algo);
                subprocess.check_call("echo 'Algorithm,"+sel_algo+",\n' >> "+output_dir+"/output", shell=True);
                summary_fp.write("Algorithm Type: "+sel_algo+",\n");
                sum = 0.0;
                count = 0;
                summary_fp.write("Start Node: [");
                for iter in range(0, args.iteration):
                    for snode in spoints:
                        summary_fp.write(snode+" ");
                        output  = execute("galois", input_graph, app, snode, exec_bin_dir, sel_algo, args.threads);
                        print (str(output));
                        log_fp.write(str(output));
                        out     = subprocess.Popen("cat perf_result", stdout=subprocess.PIPE, shell=True);
                        output  = out.communicate();
                        latency = float(output[0].split(",")[2]);
                        sum    += latency;
                        count  += 1;
                        subprocess.check_call("cat perf_result >> "+output_dir+"/output", shell=True);
                summary_fp.write("],"+str(format(sum/float(count), 'f'))+"\n");
                if best_dat[input_graph][app][0] > sum/float(count):
                    best_dat[input_graph][app][0] = sum/float(count)
                    best_dat[input_graph][app][1] = sel_algo;
    log_fp.close();
    summary_fp.close();
    summarize_best_dat(output_dir+"/summary",best_dat, args.applications, args.graphs);

if __name__=='__main__':
    main()
