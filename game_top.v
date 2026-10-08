module game_top (
    input  wire i_Clk,
    output wire [3:0] o_LED,
    input  wire [3:0] i_Switch,
    output wire o_Segment1_A, /* ... todos los segmentos 1 y 2 ... */
    input  wire i_SPI_SCLK, input  wire i_SPI_MOSI,
    input  wire i_SPI_CS_n,  output wire o_SPI_MISO
    );
    pochoco_soc #(.MemFile("sw/game.hex")) u_pochoco (
        .i_Clk(i_Clk), .o_LED(o_LED), .i_Switch(i_Switch), /* ... */
    );
endmodule