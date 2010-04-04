#! /bin/bash

if [ -f unanalysed ]; then
    ts=$(date +%Y%m%d.%H%M)
    mv unanalysed unanalysed_$ts
    ln -sf unanalysed_$ts unanalysed_prev
fi

dir_suffix_arg=
while getopts 's:' OPTION
do
    case $OPTION in
        s) dir_suffix_arg="-s $OPTARG"
        ;;
    esac
done
shift $(($OPTIND - 1))

started=`date +%c`
./make_clean.sh
time ./make_all.sh $dir_suffix_arg all && ./do_filter.sh && (python -m'apps.cn.find_unanalysed' '../terry/CCG/output/cn/filtered_corpus.txt' > unanalysed)
ended=`date +%c`

echo "Run started: $started"
echo "Run ended:   $ended"