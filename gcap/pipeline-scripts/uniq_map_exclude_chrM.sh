BEGIN {FS="\t"; OFS="\t"}; {if (/^[^@]/) {total+=1; if ($2!="4" && $3!="chrM"){ul+=1}}} END{ print ul"\t"total }