def traverse_tree(node, visitor_fn):
    """
    Recursively traverse tree-sitter node and apply visitor_fn to each node.
    """
    visitor_fn(node)
    for child in node.children:
        traverse_tree(child, visitor_fn)