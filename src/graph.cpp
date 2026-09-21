#include "graph.hpp"

#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <unordered_map>

namespace {

// Buffered character reader; the benchmark files reach a few GB so stdio
// formatted input is too slow.
struct Reader {
    FILE* f = nullptr;
    std::vector<char> buf;
    size_t pos = 0, len = 0;

    explicit Reader(FILE* file) : f(file), buf(1 << 20) {}

    int get() {
        if (pos == len) {
            len = fread(buf.data(), 1, buf.size(), f);
            pos = 0;
            if (len == 0) return -1;
        }
        return (unsigned char)buf[pos++];
    }
    void unget() { if (pos > 0) --pos; }

    // Skips whitespace and comment lines ('#', '%', 'c').  Returns false at EOF.
    bool skip_filler() {
        for (;;) {
            int c = get();
            if (c < 0) return false;
            if (c == '#' || c == '%' || c == 'c') {
                while (c >= 0 && c != '\n') c = get();
                continue;
            }
            if (isspace(c)) continue;
            unget();
            return true;
        }
    }
    // Reads a non-negative integer.  Returns false at EOF.
    bool read_int(long long& out) {
        if (!skip_filler()) return false;
        long long v = 0;
        bool any = false;
        for (;;) {
            int c = get();
            if (c < 0) break;
            if (c >= '0' && c <= '9') { v = v * 10 + (c - '0'); any = true; continue; }
            unget();
            break;
        }
        if (!any) return false;
        out = v;
        return true;
    }
    // Reads the rest of the current line into s.
    bool read_line(std::string& s) {
        s.clear();
        int c = get();
        if (c < 0) return false;
        while (c >= 0 && c != '\n') { s.push_back((char)c); c = get(); }
        return true;
    }
};

std::string lower_ext(const std::string& path) {
    size_t dot = path.find_last_of('.');
    if (dot == std::string::npos) return "";
    std::string e = path.substr(dot + 1);
    for (char& c : e) c = (char)tolower(c);
    return e;
}

// Builds CSR from an undirected edge list, removing self loops and duplicates.
void build_csr(int n, std::vector<std::pair<int, int>>& edges, Graph& g) {
    g.n = n;
    g.start.assign(n + 1, 0);
    std::vector<long long> cnt(n + 1, 0);
    for (auto& e : edges) {
        if (e.first == e.second) continue;
        cnt[e.first]++;
        cnt[e.second]++;
    }
    long long acc = 0;
    for (int v = 0; v < n; ++v) { g.start[v] = acc; acc += cnt[v]; }
    g.start[n] = acc;
    g.adj.assign(acc, 0);
    std::vector<long long> cur(g.start.begin(), g.start.end() - 1);
    for (auto& e : edges) {
        if (e.first == e.second) continue;
        g.adj[cur[e.first]++] = e.second;
        g.adj[cur[e.second]++] = e.first;
    }
    // Sort and deduplicate each adjacency list, compacting in place.
    long long write = 0;
    std::vector<long long> new_start(n + 1, 0);
    for (int v = 0; v < n; ++v) {
        long long b = g.start[v], e = g.start[v + 1];
        std::sort(g.adj.begin() + b, g.adj.begin() + e);
        new_start[v] = write;
        int prev = -1;
        for (long long i = b; i < e; ++i) {
            if (g.adj[i] == prev) continue;
            prev = g.adj[i];
            g.adj[write++] = prev;
        }
    }
    new_start[n] = write;
    g.start.swap(new_start);
    g.adj.resize(write);
    g.m = write / 2;
}

bool load_metis(Reader& r, Graph& g, std::string& err) {
    long long n = 0, m = 0;
    if (!r.read_int(n) || !r.read_int(m)) { err = "bad METIS header"; return false; }
    // An optional format field may follow on the same line; weighted files are
    // rejected because this solver is unweighted.
    std::string rest;
    r.read_line(rest);
    for (char c : rest) {
        if (!isspace((unsigned char)c)) {
            if (c != '0') { err = "weighted METIS files are not supported"; return false; }
        }
    }
    g.n = (int)n;
    g.start.assign(n + 1, 0);
    g.adj.clear();
    g.adj.reserve(2 * m);
    std::string line;
    long long v = 0;
    while (v < n && r.read_line(line)) {
        const char* p = line.c_str();
        if (*p == '%' || *p == '#') continue;  // comment lines do not count
        g.start[v] = (long long)g.adj.size();
        while (*p) {
            while (*p && !isdigit((unsigned char)*p)) ++p;
            if (!*p) break;
            long long u = 0;
            while (isdigit((unsigned char)*p)) { u = u * 10 + (*p - '0'); ++p; }
            if (u < 1 || u > n) { err = "METIS neighbour id out of range"; return false; }
            g.adj.push_back((int)(u - 1));
        }
        ++v;
    }
    while (v < n) { g.start[v] = (long long)g.adj.size(); ++v; }
    g.start[n] = (long long)g.adj.size();
    // Normalise: drop self loops / duplicates and make the file symmetric.
    std::vector<std::pair<int, int>> edges;
    edges.reserve(g.adj.size());
    for (int x = 0; x < g.n; ++x)
        for (long long i = g.start[x]; i < g.start[x + 1]; ++i)
            if (x < g.adj[i]) edges.emplace_back(x, g.adj[i]);
            else if (x > g.adj[i]) edges.emplace_back(g.adj[i], x);
    build_csr(g.n, edges, g);
    return true;
}

bool load_pairs(Reader& r, Graph& g, bool dimacs, std::string& err) {
    std::vector<std::pair<int, int>> raw;
    long long declared_n = 0;
    if (dimacs) {
        // DIMACS: "p edge n m" then "e u v" lines; 'c' lines already skipped.
        std::string line;
        for (;;) {
            if (!r.skip_filler()) break;
            int c = r.get();
            if (c < 0) break;
            if (c == 'p') {
                r.read_line(line);
                long long a = 0, b = 0;
                if (sscanf(line.c_str(), "%*s %lld %lld", &a, &b) >= 1) declared_n = a;
                continue;
            }
            if (c == 'e') {
                long long u = 0, v = 0;
                if (!r.read_int(u) || !r.read_int(v)) break;
                raw.emplace_back((int)u, (int)v);
                continue;
            }
            r.unget();
            long long u = 0, v = 0;
            if (!r.read_int(u) || !r.read_int(v)) break;
            raw.emplace_back((int)u, (int)v);
        }
    } else {
        long long u = 0, v = 0;
        while (r.read_int(u)) {
            if (!r.read_int(v)) break;
            raw.emplace_back((int)u, (int)v);
        }
    }
    if (raw.empty()) { err = "no edges found"; return false; }
    // Compact vertex ids while preserving order of first appearance is not
    // needed; a dense remap by sorted id keeps output deterministic.
    std::vector<int> ids;
    ids.reserve(raw.size() * 2);
    for (auto& e : raw) { ids.push_back(e.first); ids.push_back(e.second); }
    std::sort(ids.begin(), ids.end());
    ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
    std::unordered_map<int, int> remap;
    remap.reserve(ids.size() * 2);
    for (size_t i = 0; i < ids.size(); ++i) remap[ids[i]] = (int)i;
    int n = (int)ids.size();
    if (declared_n > n) n = (int)declared_n;  // isolated vertices declared in header
    std::vector<std::pair<int, int>> edges;
    edges.reserve(raw.size());
    for (auto& e : raw) edges.emplace_back(remap[e.first], remap[e.second]);
    build_csr(n, edges, g);
    return true;
}

bool load_mtx(Reader& r, Graph& g, std::string& err) {
    // The banner line starts with '%' and is skipped by skip_filler; the first
    // numeric triple is "rows cols nnz".
    long long rows = 0, cols = 0, nnz = 0;
    if (!r.read_int(rows) || !r.read_int(cols) || !r.read_int(nnz)) {
        err = "bad Matrix Market header";
        return false;
    }
    int n = (int)std::max(rows, cols);
    std::vector<std::pair<int, int>> edges;
    edges.reserve(nnz);
    long long u = 0, v = 0;
    while (r.read_int(u)) {
        if (!r.read_int(v)) break;
        if (u < 1 || v < 1 || u > n || v > n) { err = "Matrix Market index out of range"; return false; }
        edges.emplace_back((int)(u - 1), (int)(v - 1));
    }
    build_csr(n, edges, g);
    return true;
}

}  // namespace

bool Graph::has_edge(int u, int v) const {
    if (degree(u) > degree(v)) std::swap(u, v);
    return std::binary_search(nbr_begin(u), nbr_end(u), v);
}

bool load_graph(const std::string& path, Graph& g, std::string& err) {
    FILE* f = fopen(path.c_str(), "rb");
    if (!f) { err = "cannot open " + path + ": " + strerror(errno); return false; }
    Reader r(f);
    std::string ext = lower_ext(path);
    bool ok;
    if (ext == "graph" || ext == "metis") ok = load_metis(r, g, err);
    else if (ext == "mtx") ok = load_mtx(r, g, err);
    else if (ext == "clq" || ext == "col" || ext == "dimacs" || ext == "mis") ok = load_pairs(r, g, true, err);
    else ok = load_pairs(r, g, false, err);
    fclose(f);
    return ok;
}

bool write_metis(const std::string& path, const Graph& g, std::string& err) {
    FILE* f = fopen(path.c_str(), "wb");
    if (!f) { err = "cannot write " + path + ": " + strerror(errno); return false; }
    std::string out;
    out.reserve(1 << 22);
    char head[64];
    snprintf(head, sizeof head, "%d %lld\n", g.n, g.m);
    out += head;
    char num[16];
    for (int v = 0; v < g.n; ++v) {
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i) {
            int len = snprintf(num, sizeof num, "%d ", g.adj[i] + 1);
            out.append(num, len);
        }
        out.push_back('\n');
        if (out.size() > (1u << 22)) { fwrite(out.data(), 1, out.size(), f); out.clear(); }
    }
    fwrite(out.data(), 1, out.size(), f);
    fclose(f);
    return true;
}

Graph complement(const Graph& g) {
    Graph c;
    std::vector<std::pair<int, int>> edges;
    std::vector<char> mark(g.n, 0);
    for (int v = 0; v < g.n; ++v) {
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i) mark[g.adj[i]] = 1;
        for (int u = v + 1; u < g.n; ++u)
            if (!mark[u]) edges.emplace_back(v, u);
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i) mark[g.adj[i]] = 0;
    }
    build_csr(g.n, edges, c);
    return c;
}

bool is_independent_set(const Graph& g, const std::vector<char>& in_set, long long& size, int& bad_u, int& bad_v) {
    size = 0;
    bad_u = bad_v = -1;
    for (int v = 0; v < g.n; ++v) {
        if (!in_set[v]) continue;
        ++size;
        for (long long i = g.start[v]; i < g.start[v + 1]; ++i) {
            if (in_set[g.adj[i]]) { bad_u = v; bad_v = g.adj[i]; return false; }
        }
    }
    return true;
}

bool is_maximal(const Graph& g, const std::vector<char>& in_set, int& missed) {
    missed = -1;
    for (int v = 0; v < g.n; ++v) {
        if (in_set[v]) continue;
        bool blocked = false;
        for (long long i = g.start[v]; i < g.start[v + 1] && !blocked; ++i)
            if (in_set[g.adj[i]]) blocked = true;
        if (!blocked) { missed = v; return false; }
    }
    return true;
}
