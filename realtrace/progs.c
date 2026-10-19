#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int cmp(const void*a,const void*b){return *(int*)a-*(int*)b;}
static void mm(int n){double *A=malloc(n*n*8),*B=malloc(n*n*8),*C=calloc(n*n,8);
  for(int i=0;i<n*n;i++){A[i]=i%7;B[i]=i%5;}
  for(int i=0;i<n;i++)for(int j=0;j<n;j++){double s=0;for(int k=0;k<n;k++)s+=A[i*n+k]*B[k*n+j];C[i*n+j]=s;}
  printf("%f\n",C[n+1]);}
static void qs(int n){int*a=malloc(n*4);srand(1);for(int i=0;i<n;i++)a[i]=rand();qsort(a,n,4,cmp);printf("%d\n",a[n/2]);}
typedef struct{int to,next;}E;
static void bfs(int n,int m){int*head=malloc(n*4);E*e=malloc(m*sizeof(E));int*q=malloc(n*4);char*seen=calloc(n,1);
  memset(head,-1,n*4);unsigned x=12345;for(int i=0;i<m;i++){x=x*1103515245u+12345u;int u=(x>>8)%n;x=x*1103515245u+12345u;e[i].to=(x>>8)%n;e[i].next=head[u];head[u]=i;}
  int qh=0,qt=0;q[qt++]=0;seen[0]=1;int cnt=0;while(qh<qt){int u=q[qh++];cnt++;for(int j=head[u];j>=0;j=e[j].next){int v=e[j].to;if(!seen[v]){seen[v]=1;q[qt++]=v;}}}
  printf("%d\n",cnt);}
int main(int c,char**v){if(!strcmp(v[1],"mm"))mm(atoi(v[2]));else if(!strcmp(v[1],"qs"))qs(atoi(v[2]));else bfs(atoi(v[2]),atoi(v[3]));return 0;}
