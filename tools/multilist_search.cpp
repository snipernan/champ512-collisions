// Produce a candidate weighted-sum relation. Use verify.py to check the
// resulting full CHAMP-512 messages and their scalar parity.
// Generalized birthday search by shrinking centered-integer intervals.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
using U = __uint128_t;
using S = __int128_t;
struct Item { S value; uint32_t id; uint8_t parity; };
struct Link { uint32_t left, right; };
struct Node {
    int leaf = -1;
    std::vector<Item> items;
    std::vector<Link> links;
    std::unique_ptr<Node> left, right;
};
static U modulus;
static int exponent, list_bits, groups, position_count;
static size_t list_size;
static std::vector<U> weights;
static std::vector<int> positions;
static uint64_t pairs_examined = 0;
static auto started = std::chrono::steady_clock::now();
static double elapsed() {
    return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
}
static U parse_hex(std::string s) {
    if (s.substr(0,2)=="0x") s=s.substr(2);
    U x=0;
    for (char c:s) {
        unsigned v=(c>='0'&&c<='9')?c-'0':(c>='a'&&c<='f')?c-'a'+10:99;
        if(v>15) throw std::runtime_error("invalid hex");
        x=(x<<4)|v;
    }
    return x;
}
static U add_mod(U a,U b) { return a>=modulus-b ? a-(modulus-b) : a+b; }
static S centered(U a) { return a<=modulus/2 ? (S)a : -(S)(modulus-a); }
static void sort_items(std::vector<Item>& items) {
    std::sort(items.begin(),items.end(),[](const Item&a,const Item&b) {
        return a.value<b.value;
    });
}
static S lower_bound_value(S center,S radius) {
    S out;
    if (__builtin_sub_overflow(center,radius,&out))
        return -(S)(((U)1<<127)-1)-1;
    return out;
}
static S upper_bound_value(S center,S radius) {
    S out;
    if (__builtin_add_overflow(center,radius,&out)) return (S)(((U)1<<127)-1);
    return out;
}
static std::unique_ptr<Node> leaf(int index) {
    auto node=std::make_unique<Node>(); node->leaf=index;
    std::vector<U> sums(list_size); sums[0]=0;
    for(int j=0;j<list_bits;++j) {
        U w=weights[positions[index*list_bits+j]];
        size_t half=(size_t)1<<j;
        for(size_t i=0;i<half;++i) sums[half+i]=add_mod(sums[i],w);
    }
    node->items.reserve(list_size-1);
    for(uint32_t mask=1;mask<list_size;++mask) {
        S v=centered(sums[mask]);
        if(index>=groups/2) v=-v;
        node->items.push_back({v,mask,(uint8_t)(__builtin_popcount(mask)&1)});
    }
    sort_items(node->items);
    return node;
}
static std::unique_ptr<Node> build(int first,int count,int level) {
    if(count==1) return leaf(first);
    auto node=std::make_unique<Node>();
    node->left=build(first,count/2,level-1);
    node->right=build(first+count/2,count/2,level-1);
    auto& a=node->left->items; auto& b=node->right->items;
    S radius=(S)((modulus/2)>>(list_bits*level));
    if(radius<1) throw std::runtime_error("interval exhausted before final match");
    size_t lo=b.size(),hi=b.size();
    node->items.reserve(list_size+list_size/16);
    node->links.reserve(list_size+list_size/16);
    for(const auto& x:a) {
        S low=lower_bound_value(-x.value,radius);
        S high=upper_bound_value(-x.value,radius);
        while(lo && b[lo-1].value>=low) --lo;
        while(hi && b[hi-1].value>high) --hi;
        for(size_t j=lo;j<hi;++j) {
            ++pairs_examined;
            if(node->links.size()>=4*list_size)
                throw std::runtime_error("intermediate list cap exceeded");
            uint32_t id=(uint32_t)node->links.size();
            node->links.push_back({x.id,b[j].id});
            node->items.push_back({x.value+b[j].value,id,(uint8_t)(x.parity^b[j].parity)});
        }
    }
    std::vector<Item>().swap(a); std::vector<Item>().swap(b);
    sort_items(node->items);
    if(level>=2 || first%8==0) {
        std::cout<<"{\"status\":\"merging\",\"first_group\":"<<first
            <<",\"groups\":"<<count<<",\"level\":"<<level
            <<",\"list_entries\":"<<node->items.size()
            <<",\"seconds\":"<<elapsed()<<"}"<<std::endl;
    }
    return node;
}
static void trace(const Node&node,uint32_t id,std::vector<int>&coeff) {
    if(node.leaf>=0) {
        int sign=node.leaf<groups/2?1:-1;
        for(int j=0;j<list_bits;++j)
            if(id&((uint32_t)1<<j)) coeff[positions[node.leaf*list_bits+j]]=sign;
        return;
    }
    const Link& link=node.links[id];
    trace(*node.left,link.left,coeff); trace(*node.right,link.right,coeff);
}
int main(int argc,char**argv) {
    if(argc!=4) { std::cerr<<"input.txt output.json seed\n";return 2; }
    std::ifstream input(argv[1]); std::string s;
    input>>s; modulus=parse_hex(s); input>>exponent>>list_bits;
    if(exponent<2||exponent>9||list_bits<2||list_bits>22) return 2;
    groups=1<<exponent; list_size=(size_t)1<<list_bits;
    position_count=groups*list_bits;
    weights.reserve(position_count);
    for(int i=0;i<position_count;++i) { input>>s;weights.push_back(parse_hex(s)); }
    if(!input) return 3;
    uint64_t seed=std::stoull(argv[3]); std::mt19937_64 rng(seed);
    positions.resize(position_count); std::iota(positions.begin(),positions.end(),0);
    std::shuffle(positions.begin(),positions.end(),rng);
    try {
        auto left=build(0,groups/2,exponent-1);
        auto right=build(groups/2,groups/2,exponent-1);
        size_t i=0,j=right->items.size();
        uint32_t left_id=0,right_id=0; bool found=false;
        while(i<left->items.size() && j) {
            S sum=left->items[i].value+right->items[j-1].value;
            if(sum<0) {++i;continue;}
            if(sum>0) {--j;continue;}
            size_t end=i+1,begin=j-1;
            while(end<left->items.size()&&left->items[end].value==left->items[i].value)++end;
            while(begin&&right->items[begin-1].value==right->items[j-1].value)--begin;
            for(size_t ai=i;ai<end&&!found;++ai)
                for(size_t bi=begin;bi<j&&!found;++bi)
                    if(left->items[ai].parity==right->items[bi].parity) {
                        left_id=left->items[ai].id;right_id=right->items[bi].id;found=true;
                    }
            if(found)break;
            i=end;j=begin;
        }
        std::ofstream output(argv[2]);
        output<<"{\"status\":\""<<(found?"relation_found_not_postverified":"no_relation_this_trial")
            <<"\",\"groups\":"<<groups<<",\"list_bits\":"<<list_bits
            <<",\"leaf_list_size\":"<<list_size<<",\"positions\":"<<position_count
            <<",\"seed\":"<<seed<<",\"seconds\":"<<elapsed()
            <<",\"intermediate_pairs\":"<<pairs_examined
            <<",\"collision_verification_performed\":false";
        if(found) {
            std::vector<int> coeff(position_count,0);
            trace(*left,left_id,coeff); trace(*right,right_id,coeff);
            output<<",\"coefficients\":[";
            for(int k=0;k<position_count;++k)output<<(k?",":"")<<coeff[k];
            output<<"]";
        }
        output<<"}\n";output.close();
        std::cout<<"{\"status\":\""<<(found?"RELATION_FOUND":"NO_RELATION")
            <<"\",\"seconds\":"<<elapsed()<<"}"<<std::endl;
        return 0;
    } catch(const std::exception&e) {
        std::cerr<<e.what()<<std::endl;return 4;
    }
}
