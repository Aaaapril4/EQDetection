#!/usr/bin/awk -f
#get absolute.dat from phase.dat
BEGIN{
	
}

{
	if($1=="#"){
	   print "#",$15 > "absolute.dat"
	}
	else{
	   print $0 > "absolute.dat"
	}
}

END{
	
}