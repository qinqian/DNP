BEGIN {FS="\t"; OFS="\t"}; {if (/^[^@]/) {total+=1; if ($2!="4" &&  $3!="*"  && $5>=1){ul+=1}}} END{ print ul"\t"total }
