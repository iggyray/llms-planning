class node_db:
    def __init__(self) -> None:
        self.db = {}
        self.node_index = 0
    
    def get_node_index_str(self):
        cur_node_index = str(self.node_index)
        self.node_index += 1
        return cur_node_index
    
    def add_node(self, action, parent_id=None):
        cur_node_index = self.get_node_index_str()
        if cur_node_index in self.db:
            raise Exception('node index already exists')
        self.db[cur_node_index] = { "parent_id": parent_id, "action": action }
        return cur_node_index
    
    def get_plan(self, node_id, current_plan=None):
        if current_plan is None:
            current_plan = []
        if node_id is None:
            return current_plan
        
        current_plan.insert(0, self.db[node_id]['action'])
        next_node_id = self.db[node_id]['parent_id']

        return self.get_plan(next_node_id, current_plan)
    
# if __name__=="__main__":
#     # arrange
#     test_node_db = node_db()
#     parent_node_id = test_node_db.add_node("hi")
#     child_node_id = test_node_db.add_node("ho", parent_node_id)
#     grandchild_node_id = test_node_db.add_node("ha", child_node_id)

#     # act
#     plan_list = test_node_db.get_plan(grandchild_node_id)

#     #
#     print(' '.join(plan_list))