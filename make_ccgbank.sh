#! /bin/bash

if [[ $1 == "all" || $1 == "*" ]]; then
    SECTION=""
    TARGET="*"
elif [[ $1 =~ ^[0-9]{2}$ ]]; then
    SECTION=${1:-00}
    TARGET="chtb_${SECTION}*"
else
    TARGET=`basename $1`
fi

rm -rf ./final/${TARGET};
./t -q -lapps.cn.output -r CCGbankStyleOutput final -0 -R AugmentedPTBReader fixed_np/${TARGET}
