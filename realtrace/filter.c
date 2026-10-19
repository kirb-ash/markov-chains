/* usage: filter SKIP TAKE  -- read lackey --trace-mem output on stdin; print the page of each data access (L/S/M),
   collapsing consecutive repeats; discard the first SKIP page references and keep the next TAKE. */
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){long skip=atol(argv[1]),take=atol(argv[2]);char buf[256];unsigned long last=~0UL;long n=0;
 while(fgets(buf,sizeof buf,stdin)){char*p=buf;while(*p==' ')p++;if(*p!='L'&&*p!='S'&&*p!='M')continue;
  unsigned long pg=strtoul(p+2,NULL,16)>>12;if(pg==last)continue;last=pg;
  if(n>=skip)printf("%lu\n",pg);n++;if(n>=skip+take)break;}
 return 0;}
