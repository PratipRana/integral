
# coding: utf-8

# Device 0: "GeForce GTX TITAN X"
#   CUDA Driver Version / Runtime Version          9.1 / 9.1
#   CUDA Capability Major/Minor version number:    5.2
#   Total amount of global memory:                 12213 MBytes (12806062080 bytes)
#   (24) Multiprocessors, (128) CUDA Cores/MP:     3072 CUDA Cores
#   GPU Max Clock rate:                            1076 MHz (1.08 GHz)
#   Memory Clock rate:                             3505 Mhz
#   Memory Bus Width:                              384-bit
#   L2 Cache Size:                                 3145728 bytes
#   Maximum Texture Dimension Size (x,y,z)         1D=(65536), 2D=(65536, 65536), 3D=(4096, 4096, 4096)
#   Maximum Layered 1D Texture Size, (num) layers  1D=(16384), 2048 layers
#   Maximum Layered 2D Texture Size, (num) layers  2D=(16384, 16384), 2048 layers
#   Total amount of constant memory:               65536 bytes
#   Total amount of shared memory per block:       49152 bytes
#   Total number of registers available per block: 65536
#   Warp size:                                     32
#   Maximum number of threads per multiprocessor:  2048
#   Maximum number of threads per block:           1024
#   Max dimension size of a thread block (x,y,z): (1024, 1024, 64)
#   Max dimension size of a grid size    (x,y,z): (2147483647, 65535, 65535)
#   Maximum memory pitch:                          2147483647 bytes
#   Texture alignment:                             512 bytes
#   Concurrent copy and kernel execution:          Yes with 2 copy engine(s)
#   Run time limit on kernels:                     No
#   Integrated GPU sharing Host Memory:            No
#   Support host page-locked memory mapping:       Yes
#   Alignment requirement for Surfaces:            Yes
#   Device has ECC support:                        Disabled
#   Device supports Unified Addressing (UVA):      Yes
#   Device PCI Domain ID / Bus ID / location ID:   0 / 132 / 0
# 

# In[1]:


import pycuda.autoinit
import pycuda.driver as cuda
import numpy as np 
import pandas as pd
from pycuda.compiler import SourceModule
import math
import itertools


# In[2]:


mod = SourceModule("""
    #define N 1000
    __device__ float f(float x)
    {	
        float mu=1.0;
        float lambda=1.0;
        float fx;
        if(x>0.01){
            fx=(sqrt(lambda/(2*M_PI*pow(x,3))))*exp(((-1*lambda*pow((x-mu),2))/(2*pow(mu,2)*x)));
        }
            else
            fx=0;

        return fx;

    }
    
    __device__ float integral(float x1, float x2, float x3, float x4, float x5){
            //float x1=0,x2=0,x3=0,x4=0; /*these are the main variable, use range (-2:0.1:2) */
            float i, a=0.0, b=50, sum=0;
            /* printf("nThis program will integrate a function between two boundary limits."); */
             if (a > b) {
              i = a;
              a = b;
              b = i;
             }
             for (i = a; i < b; i += (b - a) / N) {
              float y;
              y = f(i)*f(i-x1)*f(i-x2)*f(i-x3)*f(i-x4)*f(i-x5);
              //printf("%f",y);
              sum += y * (b - a) / N;
             }
            return sum;
    }

    
    
    __global__ void doSome(float *in, int total, int d )
    { 
       
        int idx = blockIdx.x * blockDim.x + threadIdx.x; 

        if(idx >= total){
            return;
        }
        //printf ("%d:::::::\\t", idx);
       
        in[idx*(d+1)+5]=integral(in[idx*(d+1)+0],in[idx*(d+1)+1], in[idx*(d+1)+2], in[idx*(d+1)+3], in[idx*(d+1)+4]);
    }""")


# In[3]:
# for benchmark
start = cuda.Event()
end = cuda.Event()
#guassian distribution integral
n = 41 #number of steps
d = 5# number of dimentions
total = n**d
h_in = np.zeros((total,d+1), np.float32)



# In[4]:


# generate permutations
perm = np.zeros((total,d), np.float32)
i=0
for x in itertools.product(np.arange(-2.0, 2.1, 0.1), repeat=d):
    perm[i] = x
    i=i+1 


# In[5]:


# add one coloumn for reseult


h_in[:,:-1] = perm
h_in= np.reshape(h_in, total*(d+1))
print (h_in)


# In[6]:


func = mod.get_function("doSome")
d_in = cuda.mem_alloc(h_in.nbytes)


# In[7]:

cuda.memcpy_htod(d_in, h_in)

start.record()

blocksize = 16 
gridsize = math.floor(total/blocksize)+1

func(d_in, np.int32(total), np.int32(d),  block=(blocksize,1,1), grid =(gridsize,1,1))
cuda.memcpy_dtoh(h_in, d_in)
end.record()
end.synchronize()
secs = start.time_till(end)*1e-3
print ("N :",total)
print ("D :",d)
print ("%fs sec" % (secs))
# In[ ]:
results = pd.DataFrame(data=np.reshape(h_in,(total,d+1)))
results.to_csv("result_"+d+".tsv", sep="\t")


