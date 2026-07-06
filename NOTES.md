# Notes

Convolution is like looking at the matrix in a pitch black room with only a flashlight that can only shine a 3x3 section of the grid at once. The "flashlight" is the filter (or kernel), the "scanning" process is the convolution.

Flattening the grid into a single list of numbers loses which cell is next to whom. Convolution preserves the spatial relationship.

### DQN

When the network samples a batch from memory to learn, it updates its $Q$-values using the formula $Q(s, a) = r + \gamma \max_{a'}Q(s', a')$. 

Storing memory in a replay buffer
It is curious as to why we store *next_spatial* and *next_flat* if this data is only to be repeated in the subsequent state. That is, if $s \rightarrow s'$ then $s_{\textit{next\_spatial}} = s'_{\textit{spatial}}$. One reason is for **parallel GPU slicing**. With a linked list or index pointer system, gathering batches requires the CPU to traverse memory pointers or calculate index offsets.

When updating $Q$ values am i using previous $Q$ or updated $Q$?