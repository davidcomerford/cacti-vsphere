<?php

/* do NOT run this script through a web browser */
if (!isset($_SERVER["argv"][0]) || isset($_SERVER['REQUEST_METHOD'])  || isset($_SERVER['REMOTE_ADDR'])) {
	die("<br><strong>This script is only meant to run at the command line.</strong>");
}

$no_http_headers = true;

/* display No errors */
error_reporting(1);


if (isset($config)) {
	include_once(dirname(__FILE__) . "/../lib/snmp.php");
}

if (!isset($called_by_script_server)) {
	include_once(dirname(__FILE__) . "/../include/global.php");
	include_once(dirname(__FILE__) . "/../lib/snmp.php");

	array_shift($_SERVER["argv"]);

	print call_user_func_array("ss_vsphere", $_SERVER["argv"]);
}

function ss_vsphere($hostname, $snmp_auth="", $cmd="", $arg1="", $arg2="") {

	$datafilepath = '/tmp/cacti-'.$hostname.'-data.json';
	if (file_exists($datafilepath)) {
		$datafile = file_get_contents($datafilepath);
	}
	else {
		exit("Couldn't find " . $datafilepath ."\n");
	}

	$masterlist = json_decode($datafile, true); // decode the JSON into an associative array
	# DEBUG #echo print_r($masterlist, true);

	if ($cmd == "cluster") {
		foreach ($masterlist as $key => $value) {
			echo $key."\n";
		}
	}

	elseif ($cmd == "num_indexes") {
		print count($clustername);
	}

	elseif ($cmd == "query") {
		$arg = $arg1;
		$index = $arg2;

		if ($arg == "cluster") {
			foreach ($masterlist as $key => $value) {
				echo $key."!".$key."\n";
			}
		}
		else if ($arg == "cpuratio") {
			foreach ($masterlist as $key => $value) {
				echo $key."!".$value['cpuratio'];
			}
		}
		else if ($arg == "vmpoweredon") {
			foreach ($masterlist as $key => $value) {
				echo $key."!".$value['vmpoweredon'];
			}
		}
		else if ($arg == "vmpoweredoff") {
			foreach ($masterlist as $key => $value) {
				echo $key."!".$value['vmpoweredoff'];
			}
		}
	}

	elseif ($cmd == "get") {
		$arg = $arg1;
		$index = $arg2;

		if ($arg == "cpuratio") {
                        return $masterlist[$index]['cpuratio'];
		}		
		else if ($arg == "vmpoweredon") {
                        return $masterlist[$index]['vmpoweredon'];
		}		
		else if ($arg == "vmpoweredoff") {
                        return $masterlist[$index]['vmpoweredoff'];
		}
		else {
			print "Error: incorrect arguments to script";
			exit;
		}
	}
}
?>
