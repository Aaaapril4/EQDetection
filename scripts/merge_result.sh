path=/mnt/scratch/jieyaqi/alaska/final/pntf_alaska_all_iter2
outf=$path/result/phase_arrivals.csv
if [ ! -d $path/result ]; then
    mkdir $path/result
fi
if [ -a $outf ]; then
    rm $outf
fi

for resultd in `ls -d $path/result?*`
do  
    echo $resultd
    mv $resultd/*mseed $path/result
    for arrivalf in `ls $resultd/phase_arrivals*`
    do
        echo $arrivalf
        if [ ! -f $outf ]; then
            echo "create $outf"
            awk 'NR==1{print $0}' $arrivalf > $outf
        fi
        awk 'NR>1{print $0}' $arrivalf >> $outf
    done
    num=`echo $resultd | awk -F "result" '{print $2}'`
    mv $resultd/error.log $path/result/error"$num".log
    mv $path/data"$num"/* $path/data
done
