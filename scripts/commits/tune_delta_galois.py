import os
import difflib
import subprocess
import datetime

thread_no = 56;

CHUNK_LINE = "constexpr static const unsigned CHUNK_SIZE";
CCHUNK_LINE = "const int CHUNK_SIZE";
EDGE_LINE = "constexpr static const ptrdiff_t EDGE_TILE_SIZE"; 
CEDGE_LINE = "const int EDGE_TILE_SIZE"

#app_lists   = ["pr", "cc", "sssp", "bfs"]
#app_lists   = ["pr", "cc", "bfs"]
app_lists = ["sssp"]
#app_lists   = ["cc"]
file_lists  = { "bfs":{"dir":"bfs", "src":"bfs"}, \
		"cc":{"dir":"connectedcomponents", "src":"ConnectedComponents"}, \
		"pr":{"dir":"pagerank", "src":"PageRank-pull"}, \
		"sssp":{"dir":"sssp", "src":"SSSP"} };
#app_lists  = [ "cc" ]

# possible algorithm options per application
#app_algo_dics = {"bfs":["AsyncTile", "Async", "SyncTile", "Sync", "Sync2pTile","Sync2p"],
                 #"sssp":["deltaTile", "deltaStep", "serDeltaTile", "serDelta", "dijkstraTile",
                 #"dijkstra", "topo", "topoTile"],
                 #"cc":["Async", "EdgeAsync", "EdgetiledAsync", "BlockedAsync", "LabelProp", 
                 #"Serial", "Sync"],
                 #"pr":["Residual"]};
app_algo_dics = {"sssp":["deltaStep"]};
#app_algo_dics = {"bfs":["AsyncTile", "Async", "SyncTile", "Sync", "Sync2pTile","Sync2p"]};
#app_algo_dics = {"cc":["Async", "LabelProp"]}
input_graphs = ["friendster", "road-usad", "socLive", "twitter", "webGraph"];
#input_graphs = ["friendster"];
#input_graphs = ["road-usad", "socLive", "webGraph"];
#input_graphs = ["twitter", "friendster"];

# directories
src_dir      = "/h1/hlee/far_hlee/workspace/LocalGalois/lonestar/"
base_dir     = "/h1/hlee/far_hlee/workspace/LocalGalois/"
# input graphs directory
input_dir    = base_dir+"/paper_inputs/";
output_dir   = base_dir+"/paper_outputs/galois_tune_delta/";
# binary directory
bin_dir      = base_dir+"bin/";

# summarize dictionary which maintains min latencies consumed by and algorithm used by 
# each algorithm
# to sum up, the first key is graph, and the second key is application name
# and the last item is tuple of latencies and algorithm name used by the experiments
min_dic      = {};

# the number of iterations
# run as the number and calculate average
no_iter      = 1

def read_chunk_and_edges(fdir, app):
    ''' I want to pass chunk and edge tile size to 
    the simpleExecutor_galois.py due to plotting '''
    print("Reading file:"+fdir+".....");
    ce_list = {}
    with open(fdir, 'r') as _rfp:
	for line in _rfp:
	    if not app == "cc" and CHUNK_LINE in line and not "//" in line:
		ce_list["chunk"] = int(line.split("=")[1].split(";")[0].strip());
            if app == "cc" and CCHUNK_LINE in line and not "//" in line:
		ce_list["chunk"] = int(line.split("=")[1].split(";")[0].strip());
	    if not app == "cc" and EDGE_LINE in line and not "//" in line:
		ce_list["edge"] = int(line.split("=")[1].split(";")[0].strip());
	    if app == "cc" and CEDGE_LINE in line and not "//" in line:
		ce_list["edge"] = int(line.split("=")[1].split(";")[0].strip());
    return ce_list;

def get_starting_points(graph):
    """ Use the points with non-zero out degree and don't hang during execution.  """
    if graph != "friendster":
        return ["17", "38", "47", "52", "53", "58", "59", "69", "94", "96"]
    else:
        # friendster takes a long time so use fewer starting points
        return ["101", "286", "16966", "37728", "56030", "155929"]


def get_starting_points_from_file(app, graph):
    """ read start point from a file
     for bfs and sssp.
     in usual case, the start point is a node
     that has the maximum number of degrees """
    if app != "pr":
        _fname = graph+".gr.source";
    else:
        _fname = graph+".tgr.source";
    _fdir  = input_dir+_fname;
    _slist = []; 

    if not os.path.isfile(_fdir):
        print("Source file is incorrect.");

    _fp    = open(_fdir, "r");
    _snode = _fp.readline().rstrip();
    _fp.close();
    _slist.append(_snode);
    return _slist;

def readStartNode(snode_file_dir):
    """ Read start node of the graphs while bfs-ing, sssp-ing.
    Each start node is written on the *.source file 
    """
    _fp     = open(snode_file_dir, "r");
    _snode  = _fp.readline().rstrip();
    print("->Start Node:  "+ _snode);
    _fp.close();
    return _snode;

def get_cmd_galois(g, p, point, delta, bin_dir, algo_t):
    if (g in ["netflix", "netflix_2x"] and p != "cf"):
        return ""
    if (g not in ["netflix", "netflix_2x"] and p == "cf"):
        return ""

    if (p == "pr"):
        graph_path = input_dir + g + "_galois.tgr"
    elif (p == "bfs"):
        graph_path = input_dir + g + "-nw_galois.gr"
    else:
        graph_path = input_dir + g + "_galois.gr"

    args = graph_path
    if (p == "cc"):
        args += " -t="+str(thread_no)+" -noverify "
    else:
        args += " -t="+str(thread_no)+" "
    if not p == "pr":
    	args += "-algo="+algo_t+" "
#args += " -t=48 "
 
    if p == "sssp" or p == "bfs":
        args += " -startNode=" + str(point) + " -delta="+str(delta);
    elif p == "pr":
        args += " -maxIterations=21 -algo=Residual "

    command = bin_dir + " " + args;
    return command;


def get_cmd(framework, graph, app, point, delta, bin_dir, algo_t):
    ''' Construct commands
    '''
    if framework == "galois":
        cmd = get_cmd_galois(graph, app, point, delta, bin_dir, algo_t);
    return cmd;

def execute(framework, graph, app, snode, delta, bin_dir, algo_t):
    """ Execute binary file
    """
    cmd = get_cmd(framework, graph, app, snode, delta, bin_dir, algo_t);
    print(cmd);
    #subprocess.check_call(cmd, shell=True);
    out = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (output, err) = out.communicate()
    return output

def getBinFname(app):
    if app == "pr":
        return "pagerank-pull"
    elif app == "cc":
        return "connectedcomponents"
    return app;

def line_pre_adder(_fdir, n_line):
    ''' we can decide the minest number at a point where the experiments
        are finisehd. '''
    print(_fdir);
    _fp     = open(_fdir, "r");
    a_lines = _fp.readlines();
    print("==>");
    print(a_lines);
    a_lines.insert(0, n_line);
    print("-->");
    print(a_lines);
    _fp.close();

    _fp     = open(_fdir, "w");
    _fp.writelines(a_lines);
    _fp.close();
            
def write_best_results(_fdir, _dic):
    print("write best results are added");
    nl_line = ',';
    ## write application name
    for _a in app_lists:
        nl_line += _a + ",";
    nl_line += "\n";
    ## write a row which is for graph name + latency
    for _i_g in input_graphs:
        nl_line += _i_g + ",";
        for _a in app_lists:
            nl_line += str(format(_dic[_i_g][_a][0], 'f'))+",";
        nl_line += '\n';

    nl_line += ','
    for _a in app_lists:
        nl_line += _a + ",";
    nl_line += "\n";
    for _i_g in input_graphs:
        nl_line += _i_g + ",";
        for _a in app_lists:
            nl_line += str(_dic[_i_g][_a][1])+",";
        nl_line += '\n';
    line_pre_adder(_fdir, nl_line);

if __name__=='__main__':
    if os.path.isfile(output_dir+"/outputs"):
        sid = datetime.datetime.now().strftime("%fs");
        subprocess.check_call("mv "+output_dir+"/outputs "+output_dir+"/"+ \
                sid+"_outputs", shell=True);
    for input_graph in input_graphs:
	# plotting
        #spoints = get_starting_points(input_graph);
        for app in app_lists:
            if os.path.exists(output_dir+"/for_plot_"+app):
                append_write = 'a'
            else:
                append_write = 'w'
            plot_fp = open(output_dir+"/for_plot_"+app, append_write);

            # get start point from .source file
            # print(app+" , "+input_graph);
            spoints = get_starting_points_from_file(app, input_graph);
            #print(str(spoints));

            exec_dir = bin_dir+"/"+getBinFname(app);
	    #ce_list = read_chunk_and_edges(src_dir+file_lists[app]["dir"]+"/"+ \
		#			file_lists[app]["src"]+".cpp", app);
	    #CHUNK_SIZE = str(ce_list["chunk"]);
	    #if not app == "pr":
	    #	EDGET_SIZE = str(ce_list["edge"]);
	    #else:
		#EDGET_SIZE = "-1"
   	    #print(">>>>>>>> APP:"+app+", CHUNK_SIZE:"+CHUNK_SIZE+", EDGE_TILE_SIZE:"+EDGET_SIZE)
            for algo_t in app_algo_dics[app]:
                delta = 1;
                while delta <= 2048:
                    print("app:"+app+", input_g:"+input_graph+", algo:"+algo_t);
                    subprocess.check_call("echo 'Algorithm,"+algo_t+", Delta,"+str(delta)+"\n' >> "+output_dir+"/output", shell=True);
                    # to calculate average
                    sum = 0.0;
                    count = 0;
                    ##
                    for iter in range(0, no_iter):
                        for snode in spoints:
                            output  = execute("galois", input_graph, app, snode, delta, exec_dir, algo_t);
                            out     = subprocess.Popen("cat perf_result", stdout=subprocess.PIPE, shell=True);
                            output  = out.communicate();
                            latency = float(output[0].split(",")[2]);
                            sum    += latency;
                            count  += 1;
                            # format: (algo_t)_(input_graph),(chunk_size),(edge_size),(latency)
                            #plot_fp.write(algo_t+"_"+input_graph+","+CHUNK_SIZE+","+EDGET_SIZE+","+str(latency)+"\n");
                            #sum += float(output[0].split(",")[2]);
                            #print("Start Node: "+snode);
                            #print(str(latency));
                            #print(str(count)+", "+str(sum));
                            subprocess.check_call("cat perf_result >> "+output_dir+"/output", shell=True);
                    delta *= 2;        
            plot_fp.close()
    plot_fp.close();
