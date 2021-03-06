#! /bin/bash -eu

# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

function msg {
    echo "[`date +%c`] $1"
}

corpus_dir_arg=
dir_suffix_arg=
config_file_arg=
undo_topicalisation_arg=
undo_np_internal_structure_arg=

final_dir=data
while getopts 'c:s:o:C:TNh' OPTION
do
    case $OPTION in
        C) config_file_arg="-C $OPTARG" ;;
        c) corpus_dir_arg="-c $OPTARG" ;;
        s) dir_suffix_arg="-s $OPTARG" ;;
        T) undo_topicalisation_arg="-T" ;;
        N) undo_np_internal_structure_arg="-N" ;;
        o) final_dir="$OPTARG" ;;
        h) echo "$0 [-s dir-suffix] [-o output-dir] [-c corpus-dir] [-C config-file]"
           exit 1
        ;;
    esac
done
shift $(($OPTIND - 1))

started=`date +%c`
./make_clean.sh
time ./make_all.sh $corpus_dir_arg $dir_suffix_arg $config_file_arg $undo_topicalisation_arg $undo_np_internal_structure_arg all
mkdir -p $final_dir
filtered_corpus="${final_dir}/filtered_corpus"
unanalysed="${final_dir}/unanalysed"
./do_filter.sh $filtered_corpus
(python -m'apps.cn.find_unanalysed' $filtered_corpus > $unanalysed)

# Filter out derivations with [conj] leaves
msg "Filtering out derivations with [conj] leaves..."
./rmconj.py $filtered_corpus > $filtered_corpus.noconj

rm -rf ${final_dir}/{AUTO,PARG,train.piped}
mkdir -p ${final_dir}

# Kill known bad sentences
msg "Filtering rare categories and rules..."
./filter.py $filtered_corpus.noconj > $filtered_corpus.norare

msg "Creating directory structure..."
# Regroup filtered_corpus into section directories
./regroup.py $filtered_corpus.norare ${final_dir}/AUTO

msg "Creating PARGs..."
# Create PARGs
./t -q -lapps.cn.mkdeps -9 ${final_dir}/PARG $filtered_corpus.norare 2> mkdeps_errors

msg "Rebracketing (X|Y)[conj] -> X|Y[conj]..."
# Rebracket [conj] as expected by C&C: (X|Y)[conj] becomes X|Y[conj]
perl -pi -e 's/\(([^\s]+)\)\[conj\]/$1\[conj\]/g' ${final_dir}/AUTO/*/*
perl -pi -e 's/\(([^\s]+)\)\[conj\]/$1\[conj\]/g' ${final_dir}/PARG/*/*

msg "Creating supertagger data..."
# Create supertagger training data in piped format
rm -rf piped
./t -q -lapps.cn.cnc -r PipeFormat piped "%w|%P|%s" -0 ${final_dir}/AUTO/*/*
rm -rf ${final_dir}/piped
./regroup_piped.sh ${final_dir}/piped piped/*

if [ -h latest ]; then
    rm latest
fi
ln -sf ${final_dir} latest

# Check for unequal texts
msg "Checking for deleted leaves..."
python findcommon.py <(cat tagged/* | python leaves.py) <(cat ${final_dir}/AUTO/*/* | python leaves.py) 2> ${final_dir}/deleted

ended=`date +%c`

echo "Run started: $started"
echo "Run ended:   $ended"
