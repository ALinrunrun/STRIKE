# These are several parsing routines and utility methods used by STRIKE, which we consolidate here for global access.

import sys

sys.path.append("../../../code_parser/python_parser")

from run_parser import extract_dataflow, is_valid_variable_name, get_example, get_clean_code
from parser_folder import remove_comments_and_docstrings
from tree_sitter import Language, Parser

JAVA_LANGUAGE = Language(
    '../../../python_parser/parser_folder/my-languages.so',
    'java'
)

C_LANGUAGE = Language(
    '../../../python_parser/parser_folder/my-languages.so',
    'c'
)

ALL_TYPES = {
    'if_statement', 'for_statement', 'while_statement', 
    'enhanced_for_statement', 'do_statement', 'switch_expression', 'try_statement'
}

ALL_TYPES_C = {
    'if_statement', 'for_statement', 'while_statement',
    'do_statement', 'switch_statement'
}

MAX_GROUP_SIZE = 10

parser = Parser()
parser.set_language(JAVA_LANGUAGE)

parser_c = Parser()
parser_c.set_language(C_LANGUAGE)

def remove_empty_lines(code: str) -> str:
    lines = code.splitlines()
    non_empty = [line for line in lines if line.strip() != ""]
    return "\n".join(non_empty)

def if_valid_name(name):
    return is_valid_variable_name(name, "java")

def get_identifiers_list(code, without_fuc_name = False):
    results = []
    identifiers = []
    dfg, index_table, _ = extract_dataflow(code, "java")
    clean_code = get_clean_code(code, "java")
    # print(clean_code)
    seen = set()
    # print(dfg)
    for name, pos, label, *_ in dfg:
        if name not in seen and if_valid_name(name):
            if without_fuc_name and label == "method_ident":
                continue
            seen.add(name)
            if pos in index_table:
                line = index_table[pos][0][0]
                identifiers.append((name, line))
            else:
                print("identifers index error, please check!!!!!")
    for identifier_details in identifiers:
        lines = clean_code.splitlines(keepends=True)
        n = len(lines)
        identifier = identifier_details[0]
        line_pos = identifier_details[1]
        start, end = max(0, line_pos - 2), min(n, line_pos + 2)
        
        while end - start < 4 and (start > 0 or end < n):
            if start > 0: start -= 1
            elif end < n: end += 1
        
        snippet  = "".join(lines[start:end])

        # mask_snippet = get_perturbed_code(snippet, identifier, "<mask>")
            
        results.append((identifier, snippet))
    return results

def get_perturbed_code(code, tgt_word, replace_word, lang="java"):
    try:
        code = remove_comments_and_docstrings(code, lang)
    except:
        print("remove_comments_and_docstrings fails, please check!!!!!")
    perturbed_code = get_example(code, tgt_word, replace_word, lang)
    return perturbed_code

def ast_has_error(code: str, lang: str = "java") -> bool:
    if not code.strip():
        return True
    
    cur_parser = parser_c if lang == "c" else parser
    
    try:
        tree = cur_parser.parse(code.encode("utf8"))
        root = tree.root_node
    except Exception as e:
        return True

    # def print_errors(node):
    #     if node.has_error or node.type == "ERROR":
    #         print("Error:", node.type, node.start_point, node.end_point)
    #     for child in node.children:
    #         print_errors(child)
    # print_errors(root)
    
    if root.has_error:
        return True

    stack = [root]
    while stack:
        n = stack.pop()

        if n.type == "ERROR":
            return True
        
        if n.is_missing:
            return True

        if n.type == "import_declaration":
            p = n.parent
            if p is None or p.type not in ("compilation_unit", "program"):
                return True

        stack.extend(n.children)

    return False

def ast_has_error_diff(orig_code: str, new_code: str, lang: str = "java") -> bool:

    cur_parser = parser_c if lang == "c" else parser

    def collect_error_spans(code: str):
        if not code.strip():
            return {(-1, -1)}
        try:
            tree = cur_parser.parse(code.encode("utf8"))
            root = tree.root_node
        except Exception:
            return {(-1, -1)}

        errors = set()
        if root.has_error:
            errors.add((0, len(code)))

        stack = [root]
        while stack:
            n = stack.pop()
            if n.type == "ERROR" or n.is_missing:
                errors.add((n.start_byte, n.end_byte))
            stack.extend(n.children)
        return errors

    orig_errors = collect_error_spans(orig_code)
    new_errors = collect_error_spans(new_code)

    new_added = new_errors - orig_errors

    # DEBUG print
    # if new_added:
    #     print(f" new errors: ({len(new_added)})：")
    #     for s, e in sorted(new_added):
    #         snippet = new_code[s:e].replace("\n", " ")
    #         print(f"  [{s}, {e}] -> {snippet[:60]}")

    return len(new_added) > 0


def extract_statement_blocks(text, lang="java"):
    if lang == "c":
        cur_parser = parser_c
        target_types = ALL_TYPES_C     
    else:
        cur_parser = parser
        target_types = ALL_TYPES

    tree = cur_parser.parse(text.encode('utf8'))
    root = tree.root_node

    data = text.encode("utf-8")
    blocks = []
    
    def has_child_block(node):
        for c in node.children:
            if c.type in target_types:
                return True
            if has_child_block(c):
                return True
        return False
    
    def dfs(node):
        if node.type in target_types:
            #print(node.type)
            if not has_child_block(node): 
                start = node.start_byte
                end = node.end_byte
                line_start = text.rfind('\n', 0, start) + 1
                prefix = text[line_start:start]
                indent_len = start - line_start
                blockcode = data[start:end].decode("utf-8", errors="ignore")
                blocks.append((prefix + blockcode, line_start, end, indent_len))
                return
            else:
                for c in node.children:
                    dfs(c)
                return
        for c in node.children:
            dfs(c)
    
    dfs(root)
    return blocks

def extract_reorderable_blocks(code: str, lang: str = "java"):
    if lang == "c":
        cur_parser = parser_c
        decl_node = "declaration"
        call_node = "call_expression"
    else:
        cur_parser = parser
        decl_node = "local_variable_declaration"
        call_node = "method_invocation"
    
    min_len = 2
    tree = cur_parser.parse(code.encode("utf8"))
    root = tree.root_node
    data = code.encode("utf-8")
        
    def classify_statement(node):
        if node.type == decl_node:
            return "declaration"
        if node.type == "expression_statement":
            child = None
            for c in node.children:
                if c.type in {call_node, "assignment_expression"}:
                    child = c
                    break
            if child is None:
                return None
                
            if child.type == "assignment_expression":
                right = child.child_by_field_name("right")
                if right is not None and (
                    right.type.endswith("_literal")
                    or right.type in {"binary_expression", "parenthesized_expression"}
                ):
                    return "assign"
                    
            if child.type == "method_invocation":
                return "call"
        return None
        
    stmts = []
        
    def dfs(node):
        if classify_statement(node):
            stmts.append(node)
        for c in node.children:
            dfs(c)
        
    dfs(root)
    stmts.sort(key=lambda n: n.start_byte)
   
    results = []
    i = 0
    while i < len(stmts):
        current = stmts[i]
        cur_type = classify_statement(current)
        group = [current]
        i += 1
        while i < len(stmts):
            nxt = stmts[i]
            nxt_type = classify_statement(nxt)
            if nxt_type != cur_type:
                break
            gap_text = code[current.end_byte : nxt.start_byte]
            if gap_text.strip() != "":
                break
            group.append(nxt)
            current = nxt
            i += 1
        
        if len(group) >= min_len:
            def append_one(subgroup):
                start_byte = subgroup[0].start_byte
                end_byte   = subgroup[-1].end_byte
                line_start = code.rfind('\n', 0, start_byte) + 1
                indent_len = start_byte - line_start
                raw = data[start_byte:end_byte].decode("utf-8", errors="ignore")
                lines = raw.splitlines(keepends=True)
                # clean_code = "".join([l.lstrip() for l in lines])
                clean_code = "".join([l.lstrip() if l.strip() != "" else l for l in lines])
                results.append((clean_code, line_start, end_byte, indent_len))
            
            if len(group) > MAX_GROUP_SIZE:
                for j in range(0, len(group), MAX_GROUP_SIZE):
                    sub = group[j : j + MAX_GROUP_SIZE]
                    if len(sub) >= min_len:
                        append_one(sub)
            else:
                append_one(group)
        
    return results

def merge_code(orig_code, new_snippet, start, end, indent_len):
    #print("=====orignial_snippet=====")
    #print(new_snippet)
    if not new_snippet or not new_snippet.strip():
        # If the candidate is None or empty, keep the original code unchanged and set delta to 0.
        return orig_code, 0
    
    lines = new_snippet.splitlines(keepends=True)
    if not lines:  # Add an extra layer of protection
        return orig_code, 0
    
    first_line = lines[0]
    has_leading_indent = first_line.startswith((" ", "\t"))
    
    if len(lines) > 1:
        second_line = lines[1]
        next_indent = len(second_line) - len(second_line.lstrip(" \t"))
    else:
        next_indent = 0
    
    if not has_leading_indent:
        if next_indent >= indent_len:
            # Add an extra safeguard: since the second line is properly indented, only adjust the first line.
            lines[0] = " " * indent_len + lines[0]
            new_snippet = "".join(lines)
        else:
            # If the second line is under-indented (or single-line), indent the whole block.
            indent = " " * indent_len
            new_lines = [indent + line for line in lines]
            new_snippet =  "".join(new_lines)
        
    merged = orig_code[:start] + new_snippet + orig_code[end:]  
    # Length difference after insertion = inserted segment length minus original segment length
    delta = len(new_snippet) - (end - start)
    return merged, delta

def apply_replacements(code: str, repl_list):
    if isinstance(code, bytes):
        code = code.decode("utf-8", errors="ignore")
    new_code = code
    for s_b, e_b, new_l in sorted(repl_list, key=lambda x: -x[0]):
        new_code = new_code[:s_b] + new_l + new_code[e_b:]
    return new_code

def main():
    code_text = """    public static String read(ClassLoader classLoader, String name, boolean all) throws IOException {
        if (all) {
            StringMaker sm = new StringMaker();
            Enumeration enu = classLoader.getResources(name);
            while (enu.hasMoreElements()) {
                URL url = (URL) enu.nextElement();
                InputStream is = url.openStream();
                String s = read(is);
                if (s != null) {
                    sm.append(s);
                    sm.append(StringPool.NEW_LINE);
                }
                is.close();
            }
            return sm.toString().trim();
        } else {
            InputStream is = classLoader.getResourceAsStream(name);
            String s = read(is);
            is.close();
            return s;
        }
    }
"""
    idents_list = get_identifiers_list(code_text)
    identifiers = [sublist[0] for sublist in idents_list if sublist]
    # print(identifiers)
    
if __name__ == "__main__":
    main()
